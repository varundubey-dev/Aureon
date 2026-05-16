import { FcGoogle } from "react-icons/fc";

interface SocialAuthProps {
  onGoogleClick?: () => void;
}

export default function SocialAuth({
  onGoogleClick,
}: SocialAuthProps) {

  return (
    <>

      <div className="flex items-center gap-4 my-5 md:my-6">

        <div className="flex-1 h-px bg-border-primary" />

        <span className="text-xs md:text-sm text-text-muted">
          OR
        </span>

        <div className="flex-1 h-px bg-border-primary" />

      </div>

      <button
        type="button"
        onClick={onGoogleClick}
        className="w-full flex items-center justify-center gap-3 py-2.5 md:py-3 rounded-xl border border-border-secondary bg-bg-primary text-text-primary text-sm md:text-base font-medium hover:bg-bg-tertiary cursor-pointer transition-all duration-300 ease-out"
      >
        <FcGoogle size={20} />

        Continue with Google
      </button>

    </>
  );
}