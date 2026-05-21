import { useAuth } from "../../context/AuthContext";
export default function GuestHome() {
  const { user } = useAuth();

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-bg-primary px-6">
      <div className="space-y-4 text-center">
        <h1 className="text-5xl font-bold text-text-primary">Guest Session</h1>

        <p className="text-lg text-text-secondary">Limited Access Mode</p>

        <div className="space-y-1 text-sm text-text-secondary">
          <p>
            Name:{" "}
            <span className="font-medium text-text-primary">{user?.name}</span>
          </p>

          <p>
            Role:{" "}
            <span className="font-medium capitalize text-text-primary">
              Guest
            </span>
          </p>
        </div>
      </div>
    </div>
  );
}
