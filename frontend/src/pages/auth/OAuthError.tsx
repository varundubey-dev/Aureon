import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { usePageTitle } from "../../hooks/usePageTitle";

export default function OnboardingError() {
  usePageTitle("Onboarding Error");

  const navigate = useNavigate();

  useEffect(() => {
    const timeout = setTimeout(() => {
      navigate("/auth/login", {
        replace: true,
      });
    }, 4000);

    return () => clearTimeout(timeout);
  }, [navigate]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg-primary px-6">
      <div className="w-full max-w-sm rounded-2xl border border-border-primary bg-bg-secondary p-8 text-center shadow-lg">
        {/* Error Icon */}
        <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-full bg-red-500/10">
          <div className="text-2xl font-semibold text-red-500">×</div>
        </div>

        <h1 className="mb-2 text-xl font-semibold text-text-primary">
          Onboarding Failed
        </h1>

        <p className="mb-6 text-sm leading-relaxed text-text-secondary">
          Something went wrong while completing your authentication.
          Redirecting you back to login...
        </p>

        <button
          onClick={() =>
            navigate("/auth/login", {
              replace: true,
            })
          }
          className="w-full rounded-xl bg-accent-primary px-4 py-2 text-sm font-medium text-black transition-opacity hover:opacity-90"
        >
          Back to Login
        </button>
      </div>
    </div>
  );
}