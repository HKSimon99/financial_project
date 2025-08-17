"use client";

import { useState } from "react";
import { useWatchlistStore } from "../../lib/watchlist";
import { Button } from "../../src/components/ui/button";
import { Input } from "../../src/components/ui/input";

export default function WatchlistPage() {
  const { items, add, remove } = useWatchlistStore();
  const [symbol, setSymbol] = useState("");

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!symbol) return;
    await add(symbol.trim().toUpperCase());
    setSymbol("");
  };

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-xl font-bold">Watchlist</h1>
      <form onSubmit={onSubmit} className="flex gap-2">
        <Input
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          placeholder="Ticker"
        />
        <Button type="submit" disabled={!symbol}>
          Add
        </Button>
      </form>
      <ul className="space-y-2">
        {items.map((s) => (
          <li key={s} className="flex justify-between items-center border p-2">
            <span>{s}</span>
            <Button variant="secondary" onClick={() => remove(s)}>
              Remove
            </Button>
          </li>
        ))}
      </ul>
    </div>
  );
}
