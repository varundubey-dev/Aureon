import { Lock } from "lucide-react";

import AuthInput from "./AuthInput";

interface PasswordFormProps {
  password: string;
  confirmPassword: string;
  passwordError: string;
  confirmPasswordError: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

export default function PasswordForm({
  password,
  confirmPassword,
  passwordError,
  confirmPasswordError,
  onChange,
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
        showPasswordToggle
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
        showPasswordToggle
      />

    </>
  );
}