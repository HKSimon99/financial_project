"use client";

import type { ReactNode } from "react";
import "./globals.css";
import { useState, useEffect } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useWatchlistStore } from "../lib/watchlist";

export default function RootLayout({ children }: { children: ReactNode }) {
  const [queryClient] = useState(() => new QueryClient());
  const { load } = useWatchlistStore();

  useEffect(() => {
    load();
  }, [load]);

  return (
    <html lang="en">
      <body>
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      </body>
    </html>
  );
}