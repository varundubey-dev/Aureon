export interface ApiErrorResponse {
  status_code: number;
  detail: string;
  code: string;
}

export interface ApiError {
  response?: {
    data?: ApiErrorResponse;
  };
}