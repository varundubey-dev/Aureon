import { useEffect, useState } from "react";

import { useNavigate } from "react-router-dom";

import { UserRound, Mail } from "lucide-react";

import AuthInput from "../../components/auth/AuthInput";
import AuthLayout from "../../components/auth/AuthLayout";
import AuthHeader from "../../components/auth/AuthHeader";
import OtpForm from "../../components/auth/OtpForm";
import PasswordForm from "../../components/auth/PasswordForm";
import SocialAuth from "../../components/auth/SocialAuth";
import RoleSelection from "../../components/auth/RoleSelection";

import {
  signupRequest,
  verifySignupOtp,
  resendSignupOtp,
  completeSignup,
  checkUsernameAvailability,
  createGuestSession,
} from "../../services/auth_service";

import { useAuth } from "../../context/AuthContext";
import { getUserRedirectPath } from "../../utils/auth_redirects";

import {
  validateName,
  validateEmail,
  validateOtp,
  validateUsername,
  validatePassword,
  validateConfirmPassword,
} from "../../utils/auth_validators";

export default function Signup() {
  const navigate = useNavigate();
  const { loginUser, user } = useAuth();
  const [signupStep, setSignupStep] = useState(1);
  const [cooldown, setCooldown] = useState(0);
  const [signupToken, setSignupToken] = useState("");
  const [otpResent, setOtpResent] = useState(false);

  const [usernameSuggestions, setUsernameSuggestions] = useState<string[]>([]);

  const [isLoading, setIsLoading] = useState(false);

  const [isCheckingUsername, setIsCheckingUsername] = useState(false);

  const [credentials, setCredentials] = useState({
    name: "",
    username: "",
    email: "",
    otp: "",
    password: "",
    confirmPassword: "",
    role: "",
  });

  const [nameError, setNameError] = useState("");

  const [usernameError, setUsernameError] = useState("");

  const [emailError, setEmailError] = useState("");

  const [otpError, setOtpError] = useState("");

  const [passwordError, setPasswordError] = useState("");

  const [confirmPasswordError, setConfirmPasswordError] = useState("");

  const [roleError, setRoleError] = useState("");

  // Cooldown Timer
  useEffect(() => {
    if (cooldown <= 0) {
      return;
    }

    const timer = setInterval(() => {
      setCooldown((prev) => prev - 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [cooldown]);

  // Name Validation
  useEffect(() => {
    const timeout = setTimeout(() => {
      if (!credentials.name) {
        setNameError("");

        return;
      }

      setNameError(validateName(credentials.name));
    }, 500);

    return () => clearTimeout(timeout);
  }, [credentials.name]);

  // Email Validation
  useEffect(() => {
    const timeout = setTimeout(() => {
      if (!credentials.email) {
        setEmailError("");

        return;
      }

      setEmailError(validateEmail(credentials.email));
    }, 500);

    return () => clearTimeout(timeout);
  }, [credentials.email]);

  // OTP Validation
  useEffect(() => {
    if (signupStep !== 2) {
      return;
    }

    const timeout = setTimeout(() => {
      if (!credentials.otp) {
        setOtpError("");

        return;
      }

      setOtpError(validateOtp(credentials.otp));
    }, 500);

    return () => clearTimeout(timeout);
  }, [credentials.otp, signupStep]);

  // Password Validation
  useEffect(() => {
    if (signupStep !== 3) {
      return;
    }

    const timeout = setTimeout(() => {
      if (credentials.password) {
        setPasswordError(validatePassword(credentials.password));
      } else {
        setPasswordError("");
      }

      if (credentials.confirmPassword) {
        setConfirmPasswordError(
          validateConfirmPassword(
            credentials.password,
            credentials.confirmPassword,
          ),
        );
      } else {
        setConfirmPasswordError("");
      }
    }, 500);

    return () => clearTimeout(timeout);
  }, [credentials.password, credentials.confirmPassword, signupStep]);

  // Username Availability Check
  useEffect(() => {
    if (signupStep !== 3) {
      return;
    }

    const username = credentials.username.trim();

    if (!username) {
      setUsernameError("");

      return;
    }

    const validationError = validateUsername(username);

    if (validationError) {
      setUsernameError(validationError);

      return;
    }

    const timeout = setTimeout(async () => {
      try {
        setIsCheckingUsername(true);

        const response = await checkUsernameAvailability(username);

        if (!response.available) {
          setUsernameError("Username already taken");

          return;
        }

        setUsernameError("");
      } catch {
        setUsernameError("Failed to check username");
      } finally {
        setIsCheckingUsername(false);
      }
    }, 500);

    return () => clearTimeout(timeout);
  }, [credentials.username, signupStep]);

  // Input Change
  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const { name, value } = e.target;

    setCredentials((prev) => ({
      ...prev,
      [name]: value,
    }));
  }

  // Step 1 — Request Signup
  async function handleContinue() {
    const nameValidation = validateName(credentials.name);

    const emailValidation = validateEmail(credentials.email);

    setNameError(nameValidation);

    setEmailError(emailValidation);

    if (nameValidation || emailValidation) {
      return;
    }

    try {
      setIsLoading(true);

      const response = await signupRequest(credentials.name, credentials.email);

      // Existing OAuth User OR Resume Signup
      if (
        response.type === "complete_local_setup" ||
        response.type === "resume_signup"
      ) {
        setSignupToken(response.signup_token || "");

        setUsernameSuggestions(response.username_suggestions || []);

        setSignupStep(3);

        return;
      }

      setCooldown(30);

      setSignupStep(2);
    } catch (error: any) {
      const message = error?.response?.data?.detail || "Signup failed";

      setEmailError(message);
    } finally {
      setIsLoading(false);
    }
  }

  // Step 2 — Verify OTP
  async function handleVerifyOTP() {
    const otpValidation = validateOtp(credentials.otp);

    setOtpError(otpValidation);

    if (otpValidation) {
      return;
    }

    try {
      setIsLoading(true);

      const response = await verifySignupOtp(
        credentials.email,
        credentials.otp,
      );

      setSignupToken(response.signup_token);

      setUsernameSuggestions(response.username_suggestions);

      setSignupStep(3);
    } catch (error: any) {
      const message =
        error?.response?.data?.detail || "OTP verification failed";

      setOtpError(message);
    } finally {
      setIsLoading(false);
    }
  }

  // Resend OTP
  async function handleResendOtp() {
    setOtpResent(true);
    setCooldown(30);
    setOtpError("");

    try {
      await resendSignupOtp(credentials.email);
    } catch (error: any) {
      setCooldown(0);
      setOtpResent(false);

      const message = error?.response?.data?.detail || "Failed to resend OTP";

      setOtpError(message);
    }
    setTimeout(() => {
      setOtpResent(false);
    }, 3000);
  }

  // Step 3 — Credentials Validation
  function handleCredentialsContinue() {
    const usernameValidation = validateUsername(credentials.username);

    const passwordValidation = validatePassword(credentials.password);

    const confirmPasswordValidation = validateConfirmPassword(
      credentials.password,
      credentials.confirmPassword,
    );

    setUsernameError(usernameValidation);

    setPasswordError(passwordValidation);

    setConfirmPasswordError(confirmPasswordValidation);

    if (usernameValidation || passwordValidation || confirmPasswordValidation) {
      return;
    }

    if (isCheckingUsername) {
      return;
    }

    if (usernameError) {
      return;
    }

    setSignupStep(4);
  }

  // Step 4 — Complete Signup
  async function handleSignup(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();

    setRoleError("");

    if (!credentials.role) {
      setRoleError("Please select a role");

      return;
    }

    try {
      setIsLoading(true);

      const response = await completeSignup(
        signupToken,
        credentials.username,
        credentials.password,
        credentials.confirmPassword,
        credentials.role,
      );

      loginUser(response);

      navigate(getUserRedirectPath(response.user), {
        replace: true,
      });
    } catch (error: any) {
      const message = error?.response?.data?.detail || "Signup failed";

      if (message.includes("Username")) {
        setUsernameError(message);

        setSignupStep(3);

        return;
      }

      if (message.includes("Password")) {
        setPasswordError(message);

        setSignupStep(3);

        return;
      }

      setRoleError(message);
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
    } catch {
      setPasswordError("Failed to create guest session");
    } finally {
      setIsLoading(false);
    }
  }

  const currentVisibleStep =
    signupStep === 1 ? 1 : signupStep === 2 ? 2 : signupStep === 3 ? 3 : 4;

  return (
    <AuthLayout>
      <form
        noValidate
        onSubmit={handleSignup}
        className="w-full max-w-md rounded-2xl border border-border-primary bg-bg-secondary p-5 shadow-xl sm:p-6 md:p-8"
      >
        <AuthHeader
          title="Create Account"
          subtitle="Join Aureon and get started"
        />

        {/* Progress Steps */}
        {signupStep > 1 && (
          <div className="mb-7 flex items-center justify-center">
            {[1, 2, 3, 4].map((step, index) => {
              const isCompleted = step < currentVisibleStep;

              const isActive = step === currentVisibleStep;

              return (
                <div key={step} className="flex items-center">
                  <div
                    className={`
                      flex h-9 w-9 items-center justify-center rounded-full border-2 text-sm font-semibold transition-all duration-300 ease-out sm:h-10 sm:w-10
                      ${
                        isCompleted
                          ? "border-accent-primary bg-accent-primary text-accent-text"
                          : isActive
                            ? "border-accent-primary text-accent-primary"
                            : "border-border-primary text-text-secondary"
                      }
                    `}
                  >
                    {step}
                  </div>

                  {index !== 3 && (
                    <div
                      className={`
                        h-0.5 w-8 transition-all duration-300 ease-out sm:w-12 md:w-14
                        ${
                          step < currentVisibleStep
                            ? "bg-accent-primary"
                            : "bg-border-primary"
                        }
                      `}
                    />
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* STEP 1 */}
        {signupStep === 1 && (
          <>
            <AuthInput
              label="Name:"
              type="text"
              placeholder="Enter your name"
              icon={UserRound}
              error={nameError}
              value={credentials.name}
              name="name"
              onChange={handleChange}
            />

            <AuthInput
              label="Email:"
              type="email"
              placeholder="Enter your email"
              icon={Mail}
              error={emailError}
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
              {isLoading ? "Sending OTP..." : "Continue"}
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

            <div className="mt-5 text-center md:mt-6">
              <p className="text-xs text-text-secondary md:text-sm">
                Already have an account?{" "}
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
        {signupStep === 2 && (
          <OtpForm
            otp={credentials.otp}
            otpError={otpError}
            onChange={handleChange}
            onSubmit={handleVerifyOTP}
            resendCooldown={cooldown}
            onResend={handleResendOtp}
            otpResent={otpResent}
          />
        )}

        {/* STEP 3 */}
        {signupStep === 3 && (
          <>
            <AuthInput
              label="Username:"
              type="text"
              placeholder="Choose a username"
              icon={UserRound}
              error={usernameError}
              value={credentials.username}
              name="username"
              onChange={handleChange}
            />

            {/* Username Suggestions */}
            {usernameSuggestions.length > 0 && !credentials.username && (
              <div className="mb-4 flex flex-wrap gap-2">
                {usernameSuggestions.map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    onClick={() =>
                      setCredentials((prev) => ({
                        ...prev,
                        username: suggestion,
                      }))
                    }
                    className="rounded-lg border border-border-primary px-3 py-1 text-xs text-text-secondary transition-all duration-300 ease-out hover:border-accent-primary hover:text-accent-primary"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            )}

            {isCheckingUsername && (
              <p className="mb-4 text-xs text-text-secondary">
                Checking username...
              </p>
            )}

            <PasswordForm
              password={credentials.password}
              confirmPassword={credentials.confirmPassword}
              passwordError={passwordError}
              confirmPasswordError={confirmPasswordError}
              onChange={handleChange}
            />

            <button
              type="button"
              disabled={isLoading || isCheckingUsername}
              onClick={handleCredentialsContinue}
              className="mt-2 w-full cursor-pointer rounded-xl bg-accent-primary py-2.5 text-sm font-semibold text-accent-text transition-all duration-300 ease-out hover:opacity-80 disabled:cursor-not-allowed disabled:opacity-60 md:py-3 md:text-base"
            >
              Continue
            </button>
          </>
        )}

        {/* STEP 4 */}
        {signupStep === 4 && (
          <>
            <RoleSelection
              selectedRole={credentials.role}
              onSelect={(role) =>
                setCredentials((prev) => ({
                  ...prev,
                  role,
                }))
              }
              error={roleError}
            />

            <button
              type="submit"
              disabled={isLoading}
              className="mt-6 w-full cursor-pointer rounded-xl bg-accent-primary py-2.5 text-sm font-semibold text-accent-text transition-all duration-300 ease-out hover:opacity-80 disabled:cursor-not-allowed disabled:opacity-60 md:py-3 md:text-base"
            >
              {isLoading ? "Creating Account..." : "Create Account"}
            </button>
          </>
        )}
      </form>
    </AuthLayout>
  );
}
