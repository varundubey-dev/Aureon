import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { refreshSession } from "../../services/auth_service";
import { useAuth } from "../../context/AuthContext";
import { getUserRedirectPath } from "../../utils/auth_redirects";
import { usePageTitle } from "../../hooks/usePageTitle";

export default function OAuthSuccess() {
  usePageTitle("Onboarding")
  const navigate = useNavigate();

  const { loginUser } = useAuth();

  useEffect(() => {
    async function restoreSession() {
      try {
        const response = await refreshSession();

        loginUser(response);

        navigate(getUserRedirectPath(response.user), {
          replace: true,
        });
      } catch {
        navigate("/auth/login", {
          replace: true,
        });
      }
    }

    restoreSession();
  }, [loginUser, navigate]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg-primary">
      <div className="text-center">
        <div className="mb-4 h-10 w-10 animate-spin rounded-full border-2 border-border-primary border-t-accent-primary mx-auto" />

        <p className="text-sm text-text-secondary">
          Completing Google authentication...
        </p>
      </div>
    </div>
  );
}
