import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";

import { getAccessToken, setAccessToken } from "./tokenStore";

interface RetryRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  withCredentials: true,
});

// GLOBAL REFRESH LOCK
let refreshPromise: Promise<string> | null = null;

// REQUEST INTERCEPTOR Attach access token automatically
client.interceptors.request.use(
  (config) => {
    const token = getAccessToken();

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },

  (error) => Promise.reject(error),
);

// RESPONSE INTERCEPTOR Handle expired access tokens
client.interceptors.response.use(
  (response) => response,

  async (error: AxiosError) => {
    const originalRequest = error.config as RetryRequestConfig;

    // Ignore refresh endpoint itself
    const authRoutes = [
      "/auth/login",
      "/auth/signup",
      "/auth/signup/request",
      "/auth/signup/verify-otp",
      "/auth/signup/resend-otp",
      "/auth/guest",
      "/auth/refresh",
    ];

    if (authRoutes.some((route) => originalRequest?.url?.includes(route))) {
      return Promise.reject(error);
    }

    // Only handle 401 once
    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    try {
      // DEDUPE REFRESH REQUESTS
      if (!refreshPromise) {
        refreshPromise = axios
          .post(
            `${import.meta.env.VITE_API_URL}/auth/refresh`,
            {},
            {
              withCredentials: true,
            },
          )
          .then((response) => {
            const newAccessToken = response.data.access_token;

            setAccessToken(newAccessToken);

            return newAccessToken;
          })
          .finally(() => {
            refreshPromise = null;
          });
      }

      const newAccessToken = await refreshPromise;

      // Retry original request
      originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;

      return client(originalRequest);
    } catch (refreshError) {
      return Promise.reject(refreshError);
    }
  },
);

export default client;
