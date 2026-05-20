import { Headphones, Mic2 } from "lucide-react";

interface RoleSelectionProps {
  selectedRole: string;
  onSelect: (role: string) => void;
  error?: string;
}

export default function RoleSelection({
  selectedRole,
  onSelect,
  error,
}: RoleSelectionProps) {

  const roles = [
    {
      value: "listener",
      title: "Listener",
      description: "Discover and enjoy music",
      icon: Headphones,
    },
    {
      value: "artist",
      title: "Artist",
      description: "Upload and share your music",
      icon: Mic2,
    },
  ];

  return (
    <div className="mb-5 md:mb-6">

      <label className="block mb-3 text-sm text-text-secondary">
        You are:
      </label>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">

        {roles.map((role) => {

          const Icon = role.icon;

          const isSelected =
            selectedRole === role.value;

          return (
            <button
              key={role.value}
              type="button"
              onClick={() => onSelect(role.value)}
              className={`group rounded-2xl border p-4 text-left transition-all duration-300 ease-out cursor-pointer ${
                isSelected
                  ? "border-highlight-primary bg-highlight-primary/10"
                  : "border-border-primary bg-bg-primary hover:border-highlight-primary/50"
              }`}
            >

              <div className="flex items-start gap-3">

                <div className={`rounded-xl p-3 transition-all duration-300 ${
                  isSelected
                    ? "bg-highlight-primary text-white"
                    : "bg-bg-secondary text-text-secondary group-hover:text-highlight-primary"
                }`}>
                  <Icon size={22} />
                </div>

                <div>

                  <h3 className="text-sm md:text-base font-semibold text-text-primary">
                    {role.title}
                  </h3>

                  <p className="mt-1 text-xs md:text-sm text-text-secondary">
                    {role.description}
                  </p>

                </div>

              </div>

            </button>
          );
        })}

      </div>

      {error && (
        <p className="mt-2 text-sm text-danger">
          {error}
        </p>
      )}

    </div>
  );
}