import { useNavigate } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";

export default function AdminDashboard() {
  const navigate = useNavigate();

  const {
    user,
    logoutUser,
  } = useAuth();

  async function handleLogout() {
    await logoutUser();

    navigate(
      "/auth/login",
      {
        replace: true,
      },
    );
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-bg-primary px-6">
      <div className="space-y-4 text-center">
        <h1 className="text-5xl font-bold text-red-500">
          ADMIN ACCESS
        </h1>

        <p className="text-lg text-text-secondary">
          Restricted Control Panel
        </p>

        <div className="space-y-1 text-sm text-text-secondary">
          <p>
            Name:{" "}
            <span className="font-medium text-text-primary">
              {user?.name}
            </span>
          </p>

          <p>
            Role:{" "}
            <span className="font-medium capitalize text-red-400">
              Admin
            </span>
          </p>
        </div>

        <button
          onClick={handleLogout}
          className="mt-6 rounded-xl bg-red-600 px-5 py-2.5 text-sm font-semibold text-white transition-opacity hover:opacity-85"
        >
          Logout
        </button>
      </div>
    </div>
  );
}