interface AuthHeaderProps {
  title: string;
  subtitle: string;
}

export default function AuthHeader({ title, subtitle }: AuthHeaderProps) {
  return (
    <div className="relative w-full mb-7 md:mb-8 flex flex-col items-center text-center">
      <div className="relative w-full flex items-center justify-center mb-3 min-h-14">
        <img
          src="/icon.svg"
          alt="Aureon"
          className="absolute left-0 h-14 w-14 pt-2 scale-90 object-contain select-none shrink-0"
          draggable={false}
        />

        <h1 className="text-text-primary text-[1.4rem] sm:text-3xl md:text-4xl font-bold leading-none px-14">
          {title}
        </h1>
      </div>

      <p className="max-w-xs text-sm md:text-base text-text-secondary">
        {subtitle}
      </p>
    </div>
  );
}
