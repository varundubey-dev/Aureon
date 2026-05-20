import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { UserRound, Mail} from "lucide-react";

import AuthInput from "../../components/auth/AuthInput";
import AuthLayout from "../../components/auth/AuthLayout";
import AuthHeader from "../../components/auth/AuthHeader";
import OtpForm from "../../components/auth/OtpForm";
import PasswordForm from "../../components/auth/PasswordForm";
import SocialAuth from "../../components/auth/SocialAuth";
import RoleSelection from "../../components/auth/RoleSelection";

export default function Signup() {
  const navigate = useNavigate();

  const [signupStep, setSignupStep] = useState(1);
  const [cooldown, setCooldown] = useState(30);
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

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const { name, value } = e.target;

    setCredentials((prev) => ({
      ...prev,
      [name]: value,
    }));
  }

  function handleResendOtp() {
    console.log("OTP RESENT");

    setCooldown(30);
  }

  useEffect(() => {
    if (cooldown <= 0) return;

    const timer = setInterval(() => {
      setCooldown((prev) => prev - 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [cooldown]);

  function handleContinue() {
    setNameError("");
    setEmailError("");

    if (credentials.name.trim().length < 2) {
      setNameError("Name must be at least 2 characters");
      return;
    }

    if (!credentials.email.includes("@")) {
      setEmailError("Enter a valid email");
      return;
    }

    console.log("OTP SENT");

    setSignupStep(2);
  }

  function handleVerifyOTP() {
    setOtpError("");

    if (credentials.otp.length !== 6) {
      setOtpError("Enter a valid 6-digit OTP");
      return;
    }

    console.log("OTP VERIFIED");

    setSignupStep(3);
  }

  function handleCredentialsContinue() {
    setUsernameError("");
    setPasswordError("");
    setConfirmPasswordError("");

    if (credentials.username.length < 3) {
      setUsernameError("Username must be at least 3 characters");
      return;
    }

    if (credentials.password.length < 6) {
      setPasswordError("Password must be at least 6 characters");
      return;
    }

    if (credentials.password !== credentials.confirmPassword) {
      setConfirmPasswordError("Passwords do not match");
      return;
    }

    setSignupStep(4);
  }

  function handleSignup(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();

    setRoleError("");

    if (!credentials.role) {
      setRoleError("Please select a role");
      return;
    }

    console.log("ACCOUNT CREATED");
  }

  const currentVisibleStep =
    signupStep === 1 ? 1 : signupStep === 2 ? 2 : signupStep === 3 ? 3 : 4;

  return (
    <AuthLayout>
      <form noValidate
        onSubmit={handleSignup}
        className="w-full max-w-md bg-bg-secondary p-5 sm:p-6 md:p-8 rounded-2xl border border-border-primary shadow-xl"
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
                      h-9 w-9 sm:h-10 sm:w-10 rounded-full border-2
                      flex items-center justify-center text-sm font-semibold
                      transition-all duration-300 ease-out
                      ${
                        isCompleted
                          ? "bg-accent-primary border-accent-primary text-accent-text"
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
                        h-0.5 w-8 sm:w-12 md:w-14 transition-all duration-300 ease-out
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
              onClick={handleContinue}
              className="w-full mt-2 py-2.5 md:py-3 rounded-xl bg-accent-primary text-accent-text text-sm md:text-base font-semibold hover:opacity-80 cursor-pointer transition-all duration-300 ease-out"
            >
              Continue
            </button>

            <SocialAuth />

            <div className="mt-5 flex items-center gap-3">
              <div className="h-px flex-1 bg-border-primary" />

              <button
                type="button"
                onClick={() => navigate("/")}
                className="text-xs md:text-sm text-text-secondary hover:text-highlight-primary transition-all duration-300 ease-out whitespace-nowrap cursor-pointer"
              >
                Continue as Guest →
              </button>

              <div className="h-px flex-1 bg-border-primary" />
            </div>

            <div className="mt-5 md:mt-6 text-center">
              <p className="text-xs md:text-sm text-text-secondary">
                Already have an account?{" "}
                <button
                  type="button"
                  onClick={() => navigate("/auth/login")}
                  className="text-highlight-primary font-semibold hover:underline cursor-pointer transition-all duration-300 ease-out"
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

            <PasswordForm
              password={credentials.password}
              confirmPassword={credentials.confirmPassword}
              passwordError={passwordError}
              confirmPasswordError={confirmPasswordError}
              onChange={handleChange}
            />

            <button
              type="button"
              onClick={handleCredentialsContinue}
              className="w-full mt-2 py-2.5 md:py-3 rounded-xl bg-accent-primary text-accent-text text-sm md:text-base font-semibold hover:opacity-80 cursor-pointer transition-all duration-300 ease-out"
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
              className="w-full mt-6 py-2.5 md:py-3 rounded-xl bg-accent-primary text-accent-text text-sm md:text-base font-semibold hover:opacity-80 cursor-pointer transition-all duration-300 ease-out"
            >
              Create Account
            </button>
          </>
        )}
      </form>
    </AuthLayout>
  );
}
