import { useEffect } from "react";

export function usePageTitle(title: string) {
  useEffect(() => {
    document.title = `${title} - Aureon`;

    return () => {
      document.title = "Aureon";
    };
  }, [title]);
}
