import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { refreshSession } from "../../services/auth_service";
import { useAuth } from "../../context/AuthContext";
import { getUserRedirectPath } from "../../utils/auth_redirects";
import { usePageTitle } from "../../hooks/usePageTitle";
import LoadingScreen from "../../components/LoadingScreen";

export default function OAuthSuccess() {
  usePageTitle("Onboarding");

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

  return <LoadingScreen text="Hang tight while we set things up" />;
}
