import type { ReactNode } from "react";

import AuthHero from "./AuthHero";

interface AuthLayoutProps {
  children: ReactNode;
}

export default function AuthLayout({
  children,
}: AuthLayoutProps) {

  return (
    <div className="min-h-screen flex overflow-x-hidden bg-bg-primary">

      <AuthHero />

      {/* RIGHT SIDE */}
      <div className="flex-1 flex items-center justify-center p-5 md:p-6">
        {children}
      </div>

    </div>
  );
}