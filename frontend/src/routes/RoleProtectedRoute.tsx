import { Navigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

import { getUserRedirectPath } from "../utils/auth_redirects";

interface RoleProtectedRouteProps {
  children: React.ReactNode;

  allowedRoles?: string[];

  allowGuest?: boolean;

  adminOnly?: boolean;
}

export default function RoleProtectedRoute({
  children,
  allowedRoles = [],
  allowGuest = false,
  adminOnly = false,
}: RoleProtectedRouteProps) {
  const { user, isInitializing } = useAuth();

  // ==========================================
  // Wait for auth restore
  // ==========================================

  if (isInitializing) {
    return null;
  }

  // ==========================================
  // Not logged in
  // ==========================================

  if (!user) {
    return <Navigate to="/auth/login" replace />;
  }

  // ==========================================
  // Admin-only routes
  // ==========================================

  if (adminOnly) {
    if (!user.is_admin) {
      return <Navigate to={getUserRedirectPath(user)} replace />;
    }

    return children;
  }

  // ==========================================
  // Global admin bypass
  // Admin can access ALL non-admin routes
  // ==========================================

  if (user.is_admin) {
    return children;
  }

  // ==========================================
  // Guest handling
  // ==========================================

  if (user.is_guest) {
    if (!allowGuest) {
      return <Navigate to="/guest" replace />;
    }

    return children;
  }

  // ==========================================
  // Role restriction
  // ==========================================

  if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    return <Navigate to={getUserRedirectPath(user)} replace />;
  }

  return children;
}
