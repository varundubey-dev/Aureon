export interface User {
  id: string;
  name: string;
  username: string | null;
  email: string | null;
  role: string;
  is_admin: boolean;
  is_guest: boolean;
  profile_color: string;
  profile_initial: string;
  created_at: string;
}

export interface AuthResponse {
  type: string;
  user: User;
  access_token: string;
  token_type: string;
  message?: string;
}

export interface SignupRequestResponse {
  type: "otp_verification" | "complete_local_setup";
  message: string;
}

export interface SignupOtpResponse {
  message: string;
  type: "normal_signup" | "complete_local_setup";
  signup_token: string;
  username_suggestions: string[];
}

export interface SignupSessionResponse {
  message: string;
  type: "normal_signup" | "complete_local_setup";
  email: string;
  name: string;
  username_suggestions: string[];
}

export interface UsernameAvailabilityResponse {
  available: boolean;
  valid: boolean;
}

export interface PasswordResetOtpResponse {
  reset_token: string;
}

export interface OAuthOnboardingResponse {
  type: "onboarding";
  oauth_signup_token: string;
  email: string;
  name: string;
}

export interface AuthContextType {
  user: User | null;
  isInitializing: boolean;
  setUser: React.Dispatch<React.SetStateAction<User | null>>;
  loginUser: (data: AuthResponse) => void;
  logoutUser: () => Promise<void>;
}
