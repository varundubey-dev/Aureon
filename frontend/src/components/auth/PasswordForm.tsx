import { Lock } from "lucide-react";

import AuthInput from "./AuthInput";

interface PasswordFormProps {
  password: string;
  confirmPassword: string;
  passwordError: string;
  confirmPasswordError: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  submitText?: string;
}

export default function PasswordForm({
  password,
  confirmPassword,
  passwordError,
  confirmPasswordError,
  onChange,
  submitText = "Continue",
}: PasswordFormProps) {

  return (
    <>

      <AuthInput
        label="Password:"
        type="password"
        placeholder="Create a password"
        icon={Lock}
        error={passwordError}
        value={password}
        name="password"
        onChange={onChange}
      />

      <AuthInput
        label="Confirm Password:"
        type="password"
        placeholder="Confirm your password"
        icon={Lock}
        error={confirmPasswordError}
        value={confirmPassword}
        name="confirmPassword"
        onChange={onChange}
      />

      <button
        type="submit"
        className="w-full mt-2 py-2.5 md:py-3 rounded-xl bg-accent-primary text-accent-text text-sm md:text-base font-semibold hover:opacity-80 cursor-pointer transition-all duration-300 ease-out"
      >
        {submitText}
      </button>

    </>
  );
}