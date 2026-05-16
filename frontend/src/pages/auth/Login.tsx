import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { UserRound, Lock } from "lucide-react";

import AuthInput from "../../components/auth/AuthInput";
import AuthLayout from "../../components/auth/AuthLayout";
import AuthHeader from "../../components/auth/AuthHeader";
import SocialAuth from "../../components/auth/SocialAuth";

export default function Login() {

  const navigate = useNavigate();

  const [credentials, setCredentials] = useState({
    identifier: "",
    password: "",
  });

  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const { name, value } = e.target;

    setCredentials((prev) => ({
      ...prev,
      [name]: value,
    }));
  }

  function handleLogin(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();

    setEmailError("");
    setPasswordError("");

    const mockUser = {
      exists: true,
      passwordCorrect: false,
    };

    if (!mockUser.exists) {
      setEmailError("User not found");
      return;
    }

    if (!mockUser.passwordCorrect) {
      setPasswordError("Incorrect password");
      return;
    }

    console.log("LOGIN SUCCESS");
  }

  return (
    <AuthLayout>

      <form
        onSubmit={handleLogin}
        className="w-full max-w-md bg-bg-secondary p-5 sm:p-6 md:p-8 rounded-2xl border border-border-primary shadow-xl"
      >

        <AuthHeader
          title="Welcome Back!"
          subtitle="Login to your account"
        />

        <AuthInput
          label="Username or Email:"
          type="text"
          placeholder="Enter your username or email"
          icon={UserRound}
          error={emailError}
          value={credentials.identifier}
          name="identifier"
          onChange={handleChange}
        />

        <AuthInput
          label="Password:"
          type="password"
          placeholder="Enter your password"
          icon={Lock}
          error={passwordError}
          value={credentials.password}
          name="password"
          onChange={handleChange}
        />

        {/* Forgot Password */}
        <div className="flex justify-end mb-5 md:mb-6">

          <button
            type="button"
            onClick={() => navigate("/auth/forgot-password")}
            className="text-xs md:text-sm text-text-secondary hover:text-highlight-primary transition-all duration-300 ease-out"
          >
            Forgot Password?
          </button>

        </div>

        {/* Login Button */}
        <button
          type="submit"
          className="w-full py-2.5 md:py-3 rounded-xl bg-accent-primary text-accent-text text-sm md:text-base font-semibold hover:opacity-80 cursor-pointer transition-all duration-300 ease-out"
        >
          Login
        </button>

        <SocialAuth />

        {/* Signup */}
        <div className="mt-5 md:mt-6 text-center">

          <p className="text-xs md:text-sm text-text-secondary">
            Don&apos;t have an account?{" "}

            <button
              type="button"
              onClick={() => navigate("/auth/signup")}
              className="text-highlight-primary font-semibold hover:underline cursor-pointer transition-all duration-300 ease-out"
            >
              Signup
            </button>

          </p>

        </div>

      </form>

    </AuthLayout>
  );
}