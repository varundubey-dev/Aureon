interface OtpFormProps {
  otp: string;
  otpError: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onSubmit: () => void;
  buttonText?: string;
}

export default function OtpForm({
  otp,
  otpError,
  onChange,
  onSubmit,
  buttonText = "Verify OTP",
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

        {otpError && (
          <p className="mt-2 text-sm text-danger">
            {otpError}
          </p>
        )}

      </div>

      <button
        type="button"
        onClick={onSubmit}
        className="w-full py-2.5 md:py-3 rounded-xl bg-accent-primary text-accent-text text-sm md:text-base font-semibold hover:opacity-80 cursor-pointer transition-all duration-300 ease-out"
      >
        {buttonText}
      </button>

    </>
  );
}