import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getUserRedirectPath } from "../utils/auth_redirects";
import LoadingScreen from "../components/LoadingScreen";

interface AuthRouteProps {
  children: React.ReactNode;
}

export default function AuthRoute({ children }: AuthRouteProps) {
  const { user, isInitializing } = useAuth();

  // ==========================================
  // Wait for auth restore
  // ==========================================

  if (isInitializing) {
    return <LoadingScreen />;
  }

  // ==========================================
  // REAL authenticated users only
  // Guests are allowed to access auth pages
  // ==========================================

  if (user && !user.is_guest) {
    return <Navigate to={getUserRedirectPath(user)} replace />;
  }

  return children;
}
