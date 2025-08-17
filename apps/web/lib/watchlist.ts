import { create } from "zustand";
import { apiFetch } from "./api";

export type WatchlistState = {
  items: string[];
  load: () => Promise<void>;
  add: (symbol: string) => Promise<void>;
  remove: (symbol: string) => Promise<void>;
};

// Zustand store holding the watchlist and exposing async actions that
// persist to the backend. Each mutation applies optimistic updates and
// rolls back on failure.
export const useWatchlistStore = create<WatchlistState>((set, get) => ({
  items: [],
  async load() {
    try {
      const data = await apiFetch<string[]>("/api/watchlist");
      set({ items: data });
    } catch {
      // ignore loading errors
    }
  },
  async add(symbol: string) {
    const prev = get().items;
    if (prev.includes(symbol)) return;
    const optimistic = [...prev, symbol];
    set({ items: optimistic });
    try {
      await apiFetch("/api/watchlist", {
        method: "POST",
        body: JSON.stringify({ symbol }),
      });
    } catch {
      // rollback on failure
      set({ items: prev });
    }
  },
  async remove(symbol: string) {
    const prev = get().items;
    if (!prev.includes(symbol)) return;
    const optimistic = prev.filter((s) => s !== symbol);
    set({ items: optimistic });
    try {
      await apiFetch(`/api/watchlist/${symbol}`, { method: "DELETE" });
    } catch {
      // rollback on failure
      set({ items: prev });
    }
  },
}));
