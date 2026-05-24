import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { usePageTitle } from "../../hooks/usePageTitle";

import AuthLayout from "../../components/auth/AuthLayout";
import AuthHeader from "../../components/auth/AuthHeader";
import RoleSelection from "../../components/auth/RoleSelection";

import { completeGoogleSignup } from "../../services/auth_service";
import { useAuth } from "../../context/AuthContext";
import { getUserRedirectPath } from "../../utils/auth_redirects";
import { getApiError } from "../../utils/api_errors";
import { AUTH_ERRORS } from "../../constants/auth_errors";
import { toast } from "sonner";

export default function OAuthOnboarding() {
  usePageTitle("Onboarding");

  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { loginUser } = useAuth();
  const oauthSignupToken = searchParams.get("token");
  const [isLoading, setIsLoading] = useState(false);
  const [role, setRole] = useState("");
  const [errors, setErrors] = useState({
    role: "",
  });

  function setFieldError(field: keyof typeof errors, message: string) {
    setErrors((prev) => ({
      ...prev,
      [field]: message,
    }));
  }

  // Invalid OAuth session
  useEffect(() => {
    if (!oauthSignupToken) {
      navigate("/auth/login", {
        replace: true,
      });

      toast.error("Invalid OAuth session. Please try again.");
    }
  }, [oauthSignupToken, navigate]);

  // Complete OAuth signup
  async function handleContinue() {
    setFieldError("role", "");

    if (!role) {
      setFieldError("role", "Please select a role");

      return;
    }

    if (!oauthSignupToken) {
      setFieldError("role", "Invalid OAuth session");

      return;
    }

    try {
      setIsLoading(true);

      const response = await completeGoogleSignup(oauthSignupToken, role);

      loginUser(response);

      navigate(getUserRedirectPath(response.user), {
        replace: true,
      });
    } catch (error: unknown) {
      const apiError = getApiError(error);

      switch (apiError.code) {
        case AUTH_ERRORS.INVALID_SIGNUP_TOKEN:
          toast.error(
            "OAuth session expired. Please continue with Google again.",
          );

          navigate("/auth/login", {
            replace: true,
          });

          return;

        case AUTH_ERRORS.INVALID_PUBLIC_ROLE:
          setFieldError("role", apiError.detail);

          return;

        default:
          setFieldError("role", apiError.detail);
      }
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <AuthLayout>
      <div className="w-full max-w-md rounded-2xl border border-border-primary bg-bg-secondary p-5 shadow-xl sm:p-6 md:p-8">
        <AuthHeader
          title="Complete Signup"
          subtitle="Choose how you want to use Aureon"
        />

        <RoleSelection
          selectedRole={role}
          onSelect={setRole}
          error={errors.role}
        />

        <button
          type="button"
          disabled={isLoading}
          onClick={handleContinue}
          className="mt-6 w-full cursor-pointer rounded-xl bg-accent-primary py-2.5 text-sm font-semibold text-accent-text transition-all duration-300 ease-out hover:opacity-80 disabled:cursor-not-allowed disabled:opacity-60 md:py-3 md:text-base"
        >
          {isLoading ? "Completing Signup..." : "Continue"}
        </button>
      </div>
    </AuthLayout>
  );
}
