import type { ChangeEvent } from "react";
import type { LucideIcon } from "lucide-react";

type AuthInputProps = {
  label: string;
  type: string;
  placeholder: string;
  icon: LucideIcon;
  error?: string;
  value: string;
  name: string;
  onChange: (e: ChangeEvent<HTMLInputElement>) => void;
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
}: AuthInputProps) {
  return (
    <div className="mb-4 md:mb-5">

      <label className="block text-sm md:text-base text-text-secondary mb-2">
        {label}
      </label>

      <div className="relative">

        <Icon size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted" />

        <input
          type={type}
          name={name}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          className={`w-full pl-12 pr-4 py-2.5 md:py-3 rounded-xl bg-bg-primary border text-sm md:text-base text-text-primary placeholder:text-text-muted outline-none transition-all duration-300 ease-out ${
            error
              ? "border-danger focus:border-danger"
              : "border-border-primary focus:border-highlight-primary"
          }`}
        />

      </div>

      {error && (
        <span className="text-xs md:text-sm text-danger mt-2 block">
          {error}
        </span>
      )}

    </div>
  );
}