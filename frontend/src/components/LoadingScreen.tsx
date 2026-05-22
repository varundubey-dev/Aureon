export default function LoadingScreen() {
  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-bg-primary">
      {/* Ambient Glow */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute left-1/2 top-1/2 h-72 w-72 -translate-x-1/2 -translate-y-1/2 rounded-full bg-accent-primary/10 blur-3xl" />

        <div className="absolute left-[30%] top-[35%] h-40 w-40 rounded-full bg-highlight-primary/10 blur-3xl" />

        <div className="absolute bottom-[20%] right-[25%] h-52 w-52 rounded-full bg-accent-primary/10 blur-3xl" />
      </div>

      {/* Main Content */}
      <div className="relative z-10 flex flex-col items-center">
        {/* Animated Logo Circle */}
        <div className="relative flex h-20 w-20 items-center justify-center">
          {/* Outer Ring */}
          <div className="absolute inset-0 animate-spin rounded-full border border-border-primary border-t-accent-primary" />

          {/* Pulsing Core */}
          <div className="h-8 w-8 animate-pulse rounded-full bg-accent-primary shadow-[0_0_40px_var(--color-accent-primary)]" />
        </div>

        {/* Audio Visualizer */}
        <div className="mt-8 flex items-end gap-1">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className="w-1.5 animate-pulse rounded-full bg-accent-primary"
              style={{
                height: `${16 + i * 6}px`,
                animationDelay: `${i * 0.12}s`,
                animationDuration: "0.8s",
              }}
            />
          ))}
        </div>

        {/* Loading Text */}
        <div className="mt-6 space-y-2 text-center">
          <p className="text-sm font-medium text-text-primary md:text-base">
            Restoring your session
          </p>

          <p className="text-xs text-text-secondary">
            Preparing your experience...
          </p>
        </div>
      </div>
    </div>
  );
}
