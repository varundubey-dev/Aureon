import client from "../api/client";

import type {
  AuthResponse,
  SignupRequestResponse,
  SignupOtpResponse,
  SignupSessionResponse,
  UsernameAvailabilityResponse,
  PasswordResetOtpResponse,
} from "../types/auth";

export async function refreshSession() {
  const response = await client.post<AuthResponse>("/auth/refresh");

  return response.data;
}

export async function login(identifier: string, password: string) {
  const response = await client.post<AuthResponse>("/auth/login", {
    identifier,
    password,
  });

  return response.data;
}

export async function createGuestSession() {
  const response = await client.post<AuthResponse>("/auth/guest");

  return response.data;
}

export async function logout() {
  const response = await client.post("/auth/logout");

  return response.data;
}

export async function signupRequest(name: string, email: string) {
  const response = await client.post<SignupRequestResponse>(
    "/auth/signup/request",
    {
      name,
      email,
    },
  );

  return response.data;
}

export async function verifySignupOtp(email: string, otp: string) {
  const response = await client.post<SignupOtpResponse>("/auth/signup/verify", {
    email,
    otp,
  });

  return response.data;
}

export async function validateSignupSession(signupToken: string) {
  const response = await client.get<SignupSessionResponse>(
    `/auth/signup/session/${signupToken}`,
  );

  return response.data;
}

export async function resendSignupOtp(email: string) {
  const response = await client.post("/auth/signup/resend", {
    email,
  });

  return response.data;
}

export async function completeSignup(
  signup_token: string,
  username: string,
  password: string,
  confirm_password: string,
  role: string,
) {
  const response = await client.post<AuthResponse>("/auth/signup/complete", {
    signup_token,
    username,
    password,
    confirm_password,
    role,
  });

  return response.data;
}

export async function checkUsernameAvailability(username: string) {
  const response = await client.post<UsernameAvailabilityResponse>(
    "/auth/username/check",
    {
      username,
    },
  );

  return response.data;
}

export async function requestPasswordReset(email: string) {
  const response = await client.post("/auth/password-reset/request", {
    email,
  });

  return response.data;
}

export async function resendPasswordResetOtp(email: string) {
  const response = await client.post("/auth/password-reset/resend", {
    email,
  });

  return response.data;
}

export async function verifyPasswordResetOtp(email: string, otp: string) {
  const response = await client.post<PasswordResetOtpResponse>(
    "/auth/password-reset/verify",
    {
      email,
      otp,
    },
  );

  return response.data;
}

export async function completePasswordReset(
  reset_token: string,
  new_password: string,
  confirm_password: string,
) {
  const response = await client.post("/auth/password-reset/complete", {
    reset_token,
    new_password,
    confirm_password,
  });

  return response.data;
}

export function loginWithGoogle() {
  window.location.href = `${import.meta.env.VITE_API_URL}/auth/google/login`;
}

export async function completeGoogleSignup(
  oauth_signup_token: string,
  role: string,
) {
  const response = await client.post<AuthResponse>("/auth/google/complete", {
    oauth_signup_token,
    role,
  });

  return response.data;
}
