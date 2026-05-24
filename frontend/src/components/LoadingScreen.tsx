interface LoadingScreenProps {
  text?: string;
}

export default function LoadingScreen({
  text = "Hang Tight!",
}: LoadingScreenProps) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center">
      <div className="flex items-center">
        <span className="loader-dot animate-loader-1" />
        <span className="loader-dot animate-loader-2" />
        <span className="loader-dot animate-loader-3" />
      </div>

      {text && <p className="mt-6 text-sm text-text-secondary">{text}</p>}
    </div>
  );
}
