import { create } from "zustand";

type WatchlistState = {
  items: string[];
  add: (symbol: string) => void;
  remove: (symbol: string) => void;
};

export const useWatchlistStore = create<WatchlistState>((set) => ({
  items: [],
  add: (symbol) =>
    set((state) => ({
      items: state.items.includes(symbol)
        ? state.items
        : [...state.items, symbol],
    })),
  remove: (symbol) =>
    set((state) => ({
      items: state.items.filter((s) => s !== symbol),
    })),
}));