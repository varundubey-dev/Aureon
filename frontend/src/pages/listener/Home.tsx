import { useNavigate } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";

export default function Home() {
  const navigate = useNavigate();

  const { user, logoutUser } = useAuth();

  async function handleLogout() {
    await logoutUser();

    navigate("/auth/login", {
      replace: true,
    });
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-bg-primary px-6">
      <div className="space-y-4 text-center">
        <h1 className="text-5xl font-bold text-text-primary">Welcome Home</h1>

        <p className="text-lg text-text-secondary">Listener Dashboard</p>

        <div className="space-y-1 text-sm text-text-secondary">
          <p>
            Name:{" "}
            <span className="font-medium text-text-primary">{user?.name}</span>
          </p>

          <p>
            Role:{" "}
            <span className="font-medium capitalize text-text-primary">
              {user?.role}
            </span>
          </p>
        </div>

        <button
          onClick={handleLogout}
          className="mt-6 rounded-xl bg-red-500 px-5 py-2.5 text-sm font-semibold text-white transition-opacity hover:opacity-85"
        >
          Logout
        </button>
      </div>
    </div>
  );
}
