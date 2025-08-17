"use client";

import { useState } from "react";
import CompareTable from "../../src/components/compare-table";
import { Button } from "../../src/components/ui/button";
import { Input } from "../../src/components/ui/input";

export default function ComparePage() {
  const [tickers, setTickers] = useState<string[]>([]);
  const [input, setInput] = useState("");

  const addTicker = () => {
    const sym = input.trim().toUpperCase();
    if (!sym || tickers.includes(sym) || tickers.length >= 5) return;
    setTickers([...tickers, sym]);
    setInput("");
  };

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-xl font-bold">Compare</h1>
      <div className="flex gap-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ticker"
        />
        <Button onClick={addTicker} disabled={!input || tickers.length >= 5}>
          Add
        </Button>
      </div>
      <CompareTable tickers={tickers} />
    </div>
  );
}