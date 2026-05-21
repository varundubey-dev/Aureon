interface OtpFormProps {
  otp: string;
  otpError: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onSubmit: () => void;
  onResend?: () => void;
  resendCooldown?: number;
  resendDisabled?: boolean;
  buttonText?: string;
  otpResent: boolean;
}

export default function OtpForm({
  otp,
  otpError,
  onChange,
  onSubmit,
  onResend,
  resendCooldown = 0,
  resendDisabled = false,
  buttonText = "Verify OTP",
  otpResent
}: OtpFormProps) {
  return (
    <>
      <div className="mb-5">
        <label className="block mb-2 text-sm text-text-secondary">
          Enter OTP:
        </label>

        <input
          type="text"
          name="otp"
          maxLength={6}
          value={otp}
          onChange={onChange}
          placeholder="Enter 6-digit OTP"
          className="w-full rounded-xl border border-border-primary bg-bg-primary px-4 py-3 text-text-primary outline-none transition-all duration-300 focus:border-highlight-primary"
        />

        {otpError && <p className="mt-2 text-sm text-danger">{otpError}</p>}
      </div>

      <button
        type="button"
        onClick={onSubmit}
        className="w-full py-2.5 md:py-3 rounded-xl bg-accent-primary text-accent-text text-sm md:text-base font-semibold hover:opacity-80 cursor-pointer transition-all duration-300 ease-out"
      >
        {buttonText}
      </button>

      <div className="mt-4 text-center">
        {resendCooldown > 0 ? (
          <p className="text-xs md:text-sm text-text-secondary">
            Resend OTP in {resendCooldown}s
          </p>
        ) : (
          <button
            type="button"
            onClick={onResend}
            disabled={resendDisabled}
            className="cursor-pointer text-xs text-highlight-primary transition-all duration-300 ease-out hover:underline disabled:cursor-not-allowed disabled:opacity-50 md:text-sm"
          >
            {otpResent
              ? "New OTP Sent!"
              : resendCooldown > 0
                ? `Resend OTP in ${resendCooldown}s`
                : "Resend OTP"}
          </button>
        )}
      </div>
    </>
  );
}
