import { useEffect, useState } from "react";

import { useNavigate } from "react-router-dom";
import { usePageTitle } from "../../hooks/usePageTitle";

import { Mail } from "lucide-react";

import AuthInput from "../../components/auth/AuthInput";
import AuthLayout from "../../components/auth/AuthLayout";
import AuthHeader from "../../components/auth/AuthHeader";
import OtpForm from "../../components/auth/OtpForm";
import PasswordForm from "../../components/auth/PasswordForm";

import {
  requestPasswordReset,
  resendPasswordResetOtp,
  verifyPasswordResetOtp,
  completePasswordReset,
} from "../../services/auth_service";

import {
  validateEmail,
  validateOtp,
  validatePassword,
  validateConfirmPassword,
} from "../../utils/auth_validators";

import { getApiError } from "../../utils/api_errors";

import { AUTH_ERRORS } from "../../constants/auth_errors";

export default function ForgotPassword() {
  usePageTitle("Reset Password");

  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [cooldown, setCooldown] = useState(0);
  const [resetToken, setResetToken] = useState("");
  const [otpResent, setOtpResent] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [credentials, setCredentials] = useState({
    email: "",
    otp: "",
    password: "",
    confirmPassword: "",
  });

  const [errors, setErrors] = useState({
    email: "",
    otp: "",
    password: "",
    confirmPassword: "",
  });

  function setFieldError(field: keyof typeof errors, message: string) {
    setErrors((prev) => ({
      ...prev,
      [field]: message,
    }));
  }

  // Cooldown Timer
  useEffect(() => {
    if (step !== 2 || cooldown <= 0) {
      return;
    }

    const timer = setInterval(() => {
      setCooldown((prev) => prev - 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [cooldown, step]);

  // Email Validation
  useEffect(() => {
    const timeout = setTimeout(() => {
      if (!credentials.email) {
        setFieldError("email", "");

        return;
      }

      setFieldError("email", validateEmail(credentials.email));
    }, 500);

    return () => clearTimeout(timeout);
  }, [credentials.email]);

  // OTP Validation
  useEffect(() => {
    if (step !== 2) {
      return;
    }

    const timeout = setTimeout(() => {
      if (!credentials.otp) {
        setFieldError("otp", "");

        return;
      }

      setFieldError("otp", validateOtp(credentials.otp));
    }, 500);

    return () => clearTimeout(timeout);
  }, [credentials.otp, step]);

  // Password Validation
  useEffect(() => {
    if (step !== 3) {
      return;
    }

    const timeout = setTimeout(() => {
      if (credentials.password) {
        setFieldError("password", validatePassword(credentials.password));
      } else {
        setFieldError("password", "");
      }

      if (credentials.confirmPassword) {
        setFieldError(
          "confirmPassword",
          validateConfirmPassword(
            credentials.password,
            credentials.confirmPassword,
          ),
        );
      } else {
        setFieldError("confirmPassword", "");
      }
    }, 500);

    return () => clearTimeout(timeout);
  }, [credentials.password, credentials.confirmPassword, step]);

  // Input Change
  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const { name, value } = e.target;

    setCredentials((prev) => ({
      ...prev,
      [name]: value,
    }));
  }

  // Step 1 — Request Password Reset
  async function handleContinue() {
    const emailValidation = validateEmail(credentials.email);

    setFieldError("email", emailValidation);

    if (emailValidation) {
      return;
    }

    try {
      setIsLoading(true);

      await requestPasswordReset(credentials.email);

      setCooldown(30);

      setStep(2);
    } catch (error: unknown) {
      const apiError = getApiError(error);

      if (apiError.code === AUTH_ERRORS.OTP_RESEND_COOLDOWN_ACTIVE) {
        setCooldown(25);

        setStep(2);

        return;
      }

      setFieldError("email", apiError.detail);
    } finally {
      setIsLoading(false);
    }
  }

  // Resend OTP
  async function handleResendOtp() {
    setOtpResent(true);

    setCooldown(30);

    setFieldError("otp", "");

    try {
      await resendPasswordResetOtp(credentials.email);
    } catch (error: unknown) {
      setCooldown(0);

      setOtpResent(false);

      const apiError = getApiError(error);

      setFieldError("otp", apiError.detail);
    }

    setTimeout(() => {
      setOtpResent(false);
    }, 3000);
  }

  // Step 2 — Verify OTP
  async function handleVerifyOTP() {
    const otpValidation = validateOtp(credentials.otp);

    setFieldError("otp", otpValidation);

    if (otpValidation) {
      return;
    }

    try {
      setIsLoading(true);

      const response = await verifyPasswordResetOtp(
        credentials.email,
        credentials.otp,
      );

      setResetToken(response.reset_token);

      setStep(3);
    } catch (error: unknown) {
      const apiError = getApiError(error);

      setFieldError("otp", apiError.detail);
    } finally {
      setIsLoading(false);
    }
  }

  // Step 3 — Reset Password
  async function handleResetPassword(e: React.SubmitEvent<HTMLFormElement>) {
    e.preventDefault();

    const passwordValidation = validatePassword(credentials.password);

    const confirmPasswordValidation = validateConfirmPassword(
      credentials.password,
      credentials.confirmPassword,
    );

    setFieldError("password", passwordValidation);
    setFieldError("confirmPassword", confirmPasswordValidation);

    if (passwordValidation || confirmPasswordValidation) {
      return;
    }

    try {
      setIsLoading(true);

      await completePasswordReset(
        resetToken,
        credentials.password,
        credentials.confirmPassword,
      );

      navigate("/auth/login", {
        replace: true,
      });
    } catch (error: unknown) {
      const apiError = getApiError(error);

      switch (apiError.code) {
        case AUTH_ERRORS.WEAK_PASSWORD:
          setFieldError("password", apiError.detail);

          return;

        case AUTH_ERRORS.PASSWORDS_DO_NOT_MATCH:
          setFieldError("confirmPassword", apiError.detail);

          return;

        default:
          setFieldError("password", apiError.detail);
      }
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <AuthLayout>
      <form
        noValidate
        onSubmit={handleResetPassword}
        className="w-full max-w-md rounded-2xl border border-border-primary bg-bg-secondary p-5 shadow-xl sm:p-6 md:p-8"
      >
        <AuthHeader
          title="Reset Password"
          subtitle="Recover access to your account"
        />

        {/* STEP 1 */}
        {step === 1 && (
          <>
            <AuthInput
              label="Email:"
              type="email"
              placeholder="Enter your email"
              icon={Mail}
              error={errors.email}
              value={credentials.email}
              name="email"
              onChange={handleChange}
            />

            <button
              type="button"
              disabled={isLoading}
              onClick={handleContinue}
              className="mt-2 w-full cursor-pointer rounded-xl bg-accent-primary py-2.5 text-sm font-semibold text-accent-text transition-all duration-300 ease-out hover:opacity-80 disabled:cursor-not-allowed disabled:opacity-60 md:py-3 md:text-base"
            >
              {isLoading ? "Sending Reset OTP..." : "Continue"}
            </button>

            <div className="mt-5 text-center md:mt-6">
              <p className="text-xs text-text-secondary md:text-sm">
                Remembered your password?{" "}
                <button
                  type="button"
                  onClick={() => navigate("/auth/login")}
                  className="cursor-pointer font-semibold text-highlight-primary transition-all duration-300 ease-out hover:underline"
                >
                  Login
                </button>
              </p>
            </div>
          </>
        )}

        {/* STEP 2 */}
        {step === 2 && (
          <OtpForm
            otp={credentials.otp}
            otpError={errors.otp}
            onChange={handleChange}
            onSubmit={handleVerifyOTP}
            resendCooldown={cooldown}
            onResend={handleResendOtp}
            otpResent={otpResent}
          />
        )}

        {/* STEP 3 */}
        {step === 3 && (
          <>
            <PasswordForm
              password={credentials.password}
              confirmPassword={credentials.confirmPassword}
              passwordError={errors.password}
              confirmPasswordError={errors.confirmPassword}
              onChange={handleChange}
            />

            <button
              type="submit"
              disabled={isLoading}
              className="mt-2 w-full cursor-pointer rounded-xl bg-accent-primary py-2.5 text-sm font-semibold text-accent-text transition-all duration-300 ease-out hover:opacity-80 disabled:cursor-not-allowed disabled:opacity-60 md:py-3 md:text-base"
            >
              {isLoading ? "Resetting Password..." : "Reset Password"}
            </button>
          </>
        )}
      </form>
    </AuthLayout>
  );
}
