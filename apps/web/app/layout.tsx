"use client";

import type { ReactNode } from "react";
import "./globals.css";
import { useState, useEffect } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useWatchlistStore } from "../lib/watchlist";
import ThemeToggle from "@/components/theme-toggle";

export default function RootLayout({ children }: { children: ReactNode }) {
  const [queryClient] = useState(() => new QueryClient());
  const { load } = useWatchlistStore();

  useEffect(() => {
    load();
  }, [load]);

  return (
    <html lang="en" className="light">
      <body>
        <QueryClientProvider client={queryClient}>
          <div className="flex justify-end p-4">
            <ThemeToggle />
          </div>
          {children}
        </QueryClientProvider>
      </body>
    </html>
  );
}