import { FcGoogle } from "react-icons/fc";
import { loginWithGoogle } from "../../services/auth_service";

export default function SocialAuth() {
  return (
    <>
      <div className="my-5 flex items-center gap-4 md:my-6">
        <div className="h-px flex-1 bg-border-primary" />

        <span className="text-xs text-text-muted md:text-sm">OR</span>

        <div className="h-px flex-1 bg-border-primary" />
      </div>

      <button
        type="button"
        onClick={loginWithGoogle}
        className="flex w-full cursor-pointer items-center justify-center gap-3 rounded-xl border border-border-secondary bg-bg-primary py-2.5 text-sm font-medium text-text-primary transition-all duration-300 ease-out hover:bg-bg-tertiary md:py-3 md:text-base"
      >
        <FcGoogle size={20} />
        Continue with Google
      </button>
    </>
  );
}
