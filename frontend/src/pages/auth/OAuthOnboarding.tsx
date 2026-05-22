import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { usePageTitle } from "../../hooks/usePageTitle";

import AuthLayout from "../../components/auth/AuthLayout";
import AuthHeader from "../../components/auth/AuthHeader";
import RoleSelection from "../../components/auth/RoleSelection";

import { completeGoogleSignup } from "../../services/auth_service";
import { useAuth } from "../../context/AuthContext";
import { getUserRedirectPath } from "../../utils/auth_redirects";

export default function OAuthOnboarding() {
  usePageTitle("Onboarding")
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { loginUser } = useAuth();
  const [role, setRole] = useState("");
  const [roleError, setRoleError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const oauthSignupToken = searchParams.get("token");

  useEffect(() => {
    if (!oauthSignupToken) {
      navigate("/auth/login", {
        replace: true,
      });
    }
  }, [oauthSignupToken, navigate]);

  async function handleContinue() {
    setRoleError("");

    if (!role) {
      setRoleError("Please select a role");

      return;
    }

    if (!oauthSignupToken) {
      setRoleError("Invalid OAuth session");

      return;
    }

    try {
      setIsLoading(true);

      const response = await completeGoogleSignup(oauthSignupToken, role);

      loginUser(response);

      navigate(getUserRedirectPath(response.user), {
        replace: true,
      });
    } catch (error: any) {
      const message = error?.response?.data?.detail || "OAuth signup failed";

      setRoleError(message);
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
          error={roleError}
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
