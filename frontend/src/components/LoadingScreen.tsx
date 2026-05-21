export default function LoadingScreen() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-bg-primary">

      <div className="flex flex-col items-center gap-4">

        {/* Spinner */}
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-border-primary border-t-accent-primary" />

        {/* Text */}
        <p className="text-sm text-text-secondary md:text-base">
          Restoring session...
        </p>

      </div>

    </div>
  );
}