import { useState, type ChangeEvent } from "react";

import type { LucideIcon } from "lucide-react";

import { Eye, EyeOff } from "lucide-react";

type AuthInputProps = {
  label: string;
  type: string;
  placeholder: string;
  icon: LucideIcon;
  error?: string;
  value: string;
  name: string;
  onChange: (e: ChangeEvent<HTMLInputElement>) => void;
  showPasswordToggle?: boolean;
};

export default function AuthInput({
  label,
  type,
  placeholder,
  icon: Icon,
  error,
  value,
  name,
  onChange,
  showPasswordToggle = false,
}: AuthInputProps) {
  const [showPassword, setShowPassword] = useState(false);

  const inputType = showPasswordToggle && showPassword ? "text" : type;

  return (
    <div className="mb-4 md:mb-5">
      <label className="mb-2 block text-sm text-text-secondary md:text-base">
        {label}
      </label>

      <div className="relative">
        <Icon
          size={18}
          className="absolute top-1/2 left-4 -translate-y-1/2 text-text-muted"
        />

        <input
          type={inputType}
          name={name}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          className={`w-full rounded-xl border bg-bg-primary py-2.5 pl-12 text-sm text-text-primary outline-none transition-all duration-300 ease-out placeholder:text-text-muted md:py-3 md:text-base ${
            showPasswordToggle ? "pr-12" : "pr-4"
          } ${
            error
              ? "border-danger focus:border-danger"
              : "border-border-primary focus:border-highlight-primary"
          }`}
        />

        {showPasswordToggle && (
          <button
            type="button"
            onClick={() => setShowPassword((prev) => !prev)}
            className="absolute top-1/2 right-4 -translate-y-1/2 text-text-muted transition-all duration-300 ease-out hover:text-text-primary"
          >
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        )}
      </div>

      {error && (
        <span className="mt-2 block text-xs text-danger md:text-sm">
          {error}
        </span>
      )}
    </div>
  );
}
