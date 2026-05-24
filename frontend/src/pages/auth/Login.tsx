import { useEffect, useState } from "react";

import { useNavigate } from "react-router-dom";
import { usePageTitle } from "../../hooks/usePageTitle";

import { UserRound, Lock } from "lucide-react";

import AuthInput from "../../components/auth/AuthInput";
import AuthLayout from "../../components/auth/AuthLayout";
import AuthHeader from "../../components/auth/AuthHeader";
import SocialAuth from "../../components/auth/SocialAuth";

import { login, createGuestSession } from "../../services/auth_service";

import { useAuth } from "../../context/AuthContext";

import { getUserRedirectPath } from "../../utils/auth_redirects";

import {
  validateLoginIdentifier,
  validateLoginPassword,
} from "../../utils/auth_validators";

import { getApiError } from "../../utils/api_errors";
import { AUTH_ERRORS } from "../../constants/auth_errors";

export default function Login() {
  usePageTitle("Login");

  const navigate = useNavigate();

  const { loginUser, user } = useAuth();

  const [credentials, setCredentials] = useState({
    identifier: "",
    password: "",
  });

  const [errors, setErrors] = useState({
    identifier: "",
    password: "",
  });

  const [isLoading, setIsLoading] = useState(false);

  function setFieldError(field: keyof typeof errors, message: string) {
    setErrors((prev) => ({
      ...prev,
      [field]: message,
    }));
  }

  // Identifier Validation
  useEffect(() => {
    if (!credentials.identifier) {
      setFieldError("identifier", "");

      return;
    }

    const timeout = setTimeout(() => {
      setFieldError(
        "identifier",
        validateLoginIdentifier(credentials.identifier),
      );
    }, 500);

    return () => clearTimeout(timeout);
  }, [credentials.identifier]);

  // Password Validation
  useEffect(() => {
    if (!credentials.password) {
      setFieldError("password", "");

      return;
    }

    const timeout = setTimeout(() => {
      setFieldError("password", validateLoginPassword(credentials.password));
    }, 500);

    return () => clearTimeout(timeout);
  }, [credentials.password]);

  // Input Change
  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const { name, value } = e.target;

    setCredentials((prev) => ({
      ...prev,
      [name]: value,
    }));
  }

  // Login
  async function handleLogin(e: React.SubmitEvent<HTMLFormElement>) {
    e.preventDefault();

    const identifierValidation = validateLoginIdentifier(
      credentials.identifier,
    );

    const passwordValidation = validateLoginPassword(credentials.password);

    setFieldError("identifier", identifierValidation);

    setFieldError("password", passwordValidation);

    if (identifierValidation || passwordValidation) {
      return;
    }

    try {
      setIsLoading(true);

      const response = await login(
        credentials.identifier,
        credentials.password,
      );

      loginUser(response);

      navigate(getUserRedirectPath(response.user), {
        replace: true,
      });
    } catch (error: unknown) {
      const apiError = getApiError(error);

      switch (apiError.code) {
        case AUTH_ERRORS.INVALID_CREDENTIALS:
          setFieldError("password", "Incorrect username/email or password");

          return;

        case AUTH_ERRORS.SOCIAL_LOGIN_REQUIRED:
          setFieldError("identifier", apiError.detail);

          return;

        case AUTH_ERRORS.PASSWORD_LOGIN_UNAVAILABLE:
          setFieldError("password", apiError.detail);

          return;

        default:
          setFieldError("password", apiError.detail);
      }
    } finally {
      setIsLoading(false);
    }
  }

  // Guest Login
  async function handleGuestLogin() {
    if (user?.is_guest) {
      navigate("/guest", {
        replace: true,
      });

      return;
    }

    try {
      setIsLoading(true);

      const response = await createGuestSession();

      loginUser(response);

      navigate("/guest", {
        replace: true,
      });
    } catch (error: unknown) {
      const apiError = getApiError(error);

      setFieldError("password", apiError.detail);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <AuthLayout>
      <form
        noValidate
        onSubmit={handleLogin}
        className="w-full max-w-md rounded-2xl border border-border-primary bg-bg-secondary p-5 shadow-xl sm:p-6 md:px-8 md:py-4"
      >
        <AuthHeader title="Welcome Back!" subtitle="Login to your account" />

        <AuthInput
          label="Username or Email:"
          type="text"
          placeholder="Enter your username or email"
          icon={UserRound}
          error={errors.identifier}
          value={credentials.identifier}
          name="identifier"
          onChange={handleChange}
        />

        <AuthInput
          label="Password:"
          type="password"
          placeholder="Enter your password"
          icon={Lock}
          error={errors.password}
          value={credentials.password}
          name="password"
          onChange={handleChange}
          showPasswordToggle
        />

        {/* Forgot Password */}
        <div className="mb-5 flex justify-end md:mb-6">
          <button
            type="button"
            onClick={() => navigate("/auth/forgot-password")}
            className="text-xs text-text-secondary transition-all duration-300 ease-out hover:text-highlight-primary md:text-sm"
          >
            Forgot Password?
          </button>
        </div>

        {/* Login Button */}
        <button
          type="submit"
          disabled={isLoading}
          className="w-full cursor-pointer rounded-xl bg-accent-primary py-2.5 text-sm font-semibold text-accent-text transition-all duration-300 ease-out hover:opacity-80 disabled:cursor-not-allowed disabled:opacity-60 md:py-3 md:text-base"
        >
          {isLoading ? "Logging in..." : "Login"}
        </button>

        <SocialAuth />

        {/* Guest */}
        <div className="mt-5 flex items-center gap-3">
          <div className="h-px flex-1 bg-border-primary" />

          <button
            type="button"
            onClick={handleGuestLogin}
            className="cursor-pointer whitespace-nowrap text-xs text-text-secondary transition-all duration-300 ease-out hover:text-highlight-primary md:text-sm"
          >
            Continue as Guest →
          </button>

          <div className="h-px flex-1 bg-border-primary" />
        </div>

        {/* Signup */}
        <div className="mt-5 text-center md:mt-6">
          <p className="text-xs text-text-secondary md:text-sm">
            Don&apos;t have an account?{" "}
            <button
              type="button"
              onClick={() => navigate("/auth/signup")}
              className="cursor-pointer font-semibold text-highlight-primary transition-all duration-300 ease-out hover:underline"
            >
              Signup
            </button>
          </p>
        </div>
      </form>
    </AuthLayout>
  );
}
