import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Mail } from "lucide-react";

import AuthInput from "../../components/auth/AuthInput";
import AuthLayout from "../../components/auth/AuthLayout";
import AuthHeader from "../../components/auth/AuthHeader";
import OtpForm from "../../components/auth/OtpForm";
import PasswordForm from "../../components/auth/PasswordForm";

export default function ForgotPassword() {

  const navigate = useNavigate();

  const [step, setStep] = useState(1);

  const [cooldown, setCooldown] = useState(30);

  const [credentials, setCredentials] = useState({
    email: "",
    otp: "",
    password: "",
    confirmPassword: "",
  });

  const [emailError, setEmailError] = useState("");
  const [otpError, setOtpError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [confirmPasswordError, setConfirmPasswordError] = useState("");

  useEffect(() => {

    if (step !== 2) return;

    if (cooldown <= 0) return;

    const timer = setInterval(() => {

      setCooldown((prev) => prev - 1);

    }, 1000);

    return () => clearInterval(timer);

  }, [cooldown, step]);

  function handleChange(
    e: React.ChangeEvent<HTMLInputElement>,
  ) {

    const { name, value } = e.target;

    setCredentials((prev) => ({
      ...prev,
      [name]: value,
    }));
  }

  function handleContinue() {

    setEmailError("");

    if (!credentials.email.includes("@")) {

      setEmailError("Enter a valid email");

      return;
    }

    console.log("RESET OTP SENT");

    setCooldown(30);

    setStep(2);
  }

  function handleResendOtp() {

    console.log("RESET OTP RESENT");

    setCooldown(30);
  }

  function handleVerifyOTP() {

    setOtpError("");

    if (credentials.otp.length !== 6) {

      setOtpError("Enter a valid 6-digit OTP");

      return;
    }

    console.log("OTP VERIFIED");

    setStep(3);
  }

  function handleResetPassword(
    e: React.FormEvent<HTMLFormElement>,
  ) {

    e.preventDefault();

    setPasswordError("");
    setConfirmPasswordError("");

    if (credentials.password.length < 6) {

      setPasswordError(
        "Password must be at least 6 characters",
      );

      return;
    }

    if (
      credentials.password !==
      credentials.confirmPassword
    ) {

      setConfirmPasswordError(
        "Passwords do not match",
      );

      return;
    }

    console.log("PASSWORD RESET SUCCESS");

    navigate("/auth/login");
  }

  return (
    <AuthLayout>

      <form noValidate
        onSubmit={handleResetPassword}
        className="w-full max-w-md bg-bg-secondary p-5 sm:p-6 md:p-8 rounded-2xl border border-border-primary shadow-xl"
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

            <div className="mt-5 md:mt-6 text-center">

              <p className="text-xs md:text-sm text-text-secondary">
                Remembered your password?{" "}

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
        {step === 2 && (
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
        {step === 3 && (
          <>

            <PasswordForm
              password={credentials.password}
              confirmPassword={credentials.confirmPassword}
              passwordError={passwordError}
              confirmPasswordError={confirmPasswordError}
              onChange={handleChange}
            />

            <button
              type="submit"
              className="w-full mt-2 py-2.5 md:py-3 rounded-xl bg-accent-primary text-accent-text text-sm md:text-base font-semibold hover:opacity-80 cursor-pointer transition-all duration-300 ease-out"
            >
              Reset Password
            </button>

          </>
        )}

      </form>

    </AuthLayout>
  );
}