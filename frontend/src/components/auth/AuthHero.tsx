export default function AuthHero() {
  return (
    <div className="hidden md:flex flex-1 relative overflow-hidden bg-auth-hero">

      {/* Background */}
      <div className="absolute inset-0 bg-auth-gradient" />

      {/* Ambient Light */}
      <div className="absolute top-1/2 left-1/2 h-auth-glow w-auth-glow -translate-x-1/2 -translate-y-1/2 rounded-full bg-auth-light blur-auth-glow" />

      {/* Circular Grid */}
      <div
        className="absolute inset-0"
        style={{
          backgroundImage: `
            linear-gradient(to right, rgba(255,255,255,0.12) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255,255,255,0.12) 1px, transparent 1px)
          `,
          backgroundSize: "52px 52px",
          maskImage:
            "radial-gradient(circle at center, black 35%, transparent 90%)",
          WebkitMaskImage:
            "radial-gradient(circle at center, black 35%, transparent 90%)",
        }}
      />

      {/* Content */}
      <div className="relative z-10 flex flex-col items-center justify-center w-full px-10 text-center">

        {/* Logo */}
        <img
          src="/logo-gold.svg"
          alt="Aureon"
          className="w-auth-logo-sm lg:w-auth-logo-md xl:w-auth-logo-lg object-contain select-none drop-shadow-auth-logo"
          draggable={false}
        />

        {/* Typography */}
        <div className="mt-12 max-w-xl">

          <h2 className="text-white text-4xl font-semibold tracking-tight leading-[1.05]">
            Clarity In Motion.
          </h2>

          <p className="mt-6 text-base leading-relaxed text-white/45">
            A modern space where atmosphere and interaction feel seamless.
          </p>

        </div>

      </div>

    </div>
  );
}