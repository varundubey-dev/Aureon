import { useEffect } from "react";

export function usePageTitle(title: string) {
  useEffect(() => {
    document.title = `Aureon - ${title}`;

    return () => {
      document.title = "Aureon";
    };
  }, [title]);
}
