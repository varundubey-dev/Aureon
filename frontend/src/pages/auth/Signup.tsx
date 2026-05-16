import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { UserRound, Mail } from "lucide-react";

import AuthInput from "../../components/auth/AuthInput";
import AuthLayout from "../../components/auth/AuthLayout";
import AuthHeader from "../../components/auth/AuthHeader";
import OtpForm from "../../components/auth/OtpForm";
import PasswordForm from "../../components/auth/PasswordForm";
import SocialAuth from "../../components/auth/SocialAuth";

export default function Signup() {

  const navigate = useNavigate();

  const [signupStep, setSignupStep] = useState(1);

  const [credentials, setCredentials] = useState({
    username: "",
    email: "",
    otp: "",
    password: "",
    confirmPassword: "",
  });

  const [usernameError, setUsernameError] = useState("");
  const [emailError, setEmailError] = useState("");
  const [otpError, setOtpError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [confirmPasswordError, setConfirmPasswordError] = useState("");

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const { name, value } = e.target;

    setCredentials((prev) => ({
      ...prev,
      [name]: value,
    }));
  }

  function handleContinue() {

    setUsernameError("");
    setEmailError("");

    if (credentials.username.length < 3) {
      setUsernameError("Username must be at least 3 characters");
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

  function handleSignup(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();

    setPasswordError("");
    setConfirmPasswordError("");

    if (credentials.password.length < 6) {
      setPasswordError("Password must be at least 6 characters");
      return;
    }

    if (credentials.password !== credentials.confirmPassword) {
      setConfirmPasswordError("Passwords do not match");
      return;
    }

    console.log("ACCOUNT CREATED");
  }

  return (
    <AuthLayout>

      <form
        onSubmit={handleSignup}
        className="w-full max-w-md bg-bg-secondary p-5 sm:p-6 md:p-8 rounded-2xl border border-border-primary shadow-xl"
      >

        <AuthHeader
          title="Create Account"
          subtitle="Join Aureon and get started"
        />

        {signupStep === 1 && (
          <>

            <AuthInput
              label="Username:"
              type="text"
              placeholder="Enter your username"
              icon={UserRound}
              error={usernameError}
              value={credentials.username}
              name="username"
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

        {signupStep === 2 && (
          <OtpForm
            otp={credentials.otp}
            otpError={otpError}
            onChange={handleChange}
            onSubmit={handleVerifyOTP}
          />
        )}

        {signupStep === 3 && (
          <PasswordForm
            password={credentials.password}
            confirmPassword={credentials.confirmPassword}
            passwordError={passwordError}
            confirmPasswordError={confirmPasswordError}
            onChange={handleChange}
            submitText="Create Account"
          />
        )}

      </form>

    </AuthLayout>
  );
}