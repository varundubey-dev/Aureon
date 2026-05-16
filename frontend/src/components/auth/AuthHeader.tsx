interface AuthHeaderProps {
  title: string;
  subtitle: string;
}

export default function AuthHeader({
  title,
  subtitle,
}: AuthHeaderProps) {

  return (
    <div className="mb-7 md:mb-8 flex flex-col items-center text-center">

      <div className="flex flex-wrap items-center justify-center gap-2 mb-3">

        <img
          src="/icon.svg"
          alt="Aureon"
          className="h-14 w-14 scale-90 object-contain select-none shrink-0"
          draggable={false}
        />

        <h1 className="text-text-primary text-[1.7rem] sm:text-3xl md:text-4xl font-bold leading-none">
          {title}
        </h1>

      </div>

      <p className="max-w-xs text-sm md:text-base text-text-secondary">
        {subtitle}
      </p>

    </div>
  );
}