import { Routes, Route, Navigate } from "react-router-dom";

import AuthRoute from "./routes/AuthRoute";
import RoleProtectedRoute from "./routes/RoleProtectedRoute";

import Login from "./pages/auth/Login";
import Signup from "./pages/auth/Signup";
import ForgotPassword from "./pages/auth/ForgotPassword";

import Home from "./pages/listener/Home";
import ArtistDashboard from "./pages/artist/ArtistDashboard";
import GuestHome from "./pages/guest/GuestHome";
import AdminDashboard from "./pages/admin/AdminDashboard";

export default function App() {
  return (
    <Routes>

      <Route path="/auth/login"
        element={
          <AuthRoute>
            <Login />
          </AuthRoute>
        }
      />

      <Route path="/auth/signup"
        element={
          <AuthRoute>
            <Signup />
          </AuthRoute>
        }
      />

      <Route path="/auth/forgot-password"
        element={
          <AuthRoute>
            <ForgotPassword />
          </AuthRoute>
        }
      />

      <Route path="/home"
        element={
          <RoleProtectedRoute allowedRoles={["listener"]}>
            <Home />
          </RoleProtectedRoute>
        }
      />

      <Route path="/artist/dashboard"
        element={
          <RoleProtectedRoute allowedRoles={["artist"]}>
            <ArtistDashboard />
          </RoleProtectedRoute>
        }
      />

      <Route path="/guest"
        element={
          <RoleProtectedRoute allowGuest>
            <GuestHome />
          </RoleProtectedRoute>
        }
      />

      <Route path="/admin"
        element={
          <RoleProtectedRoute adminOnly>
            <AdminDashboard />
          </RoleProtectedRoute>
        }
      />

      <Route path="*" element={<Navigate to="/auth/login" replace />} />
    </Routes>
  );
}
