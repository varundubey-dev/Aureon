import type { ApiError, ApiErrorResponse } from "../types/api";

import { AUTH_ERRORS } from "../constants/auth_errors";

export type AuthErrorCode = (typeof AUTH_ERRORS)[keyof typeof AUTH_ERRORS];

export function getApiError(error: unknown): ApiErrorResponse {
  const apiError = error as ApiError;

  return {
    status_code: apiError.response?.data?.status_code ?? 500,

    detail: apiError.response?.data?.detail ?? "Something went wrong",

    code: apiError.response?.data?.code ?? "UNKNOWN_ERROR",
  };
}

export function isApiErrorCode(error: unknown, code: AuthErrorCode): boolean {
  return getApiError(error).code === code;
}
