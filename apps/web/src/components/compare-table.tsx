"use client";

import { useEffect, useState } from "react";
import MiniChart from "./mini-chart";
import { apiFetch } from "../../lib/api";

interface Snapshot {
  slug: string;
  snapshot?: { [key: string]: any };
}

export default function CompareTable({ tickers }: { tickers: string[] }) {
  const [data, setData] = useState<Record<string, Snapshot>>({});

  useEffect(() => {
    tickers.forEach(async (t) => {
      try {
        const snap = await apiFetch<Snapshot>(`/api/instrument/${t}/snapshot`);
        setData((prev) => ({ ...prev, [t]: snap }));
      } catch {
        /* ignore */
      }
    });
  }, [tickers]);

  if (!tickers.length) return <p>No tickers selected.</p>;

  return (
    <table className="min-w-full border">
      <thead>
        <tr className="bg-gray-100">
          <th className="p-2 text-left">Ticker</th>
          <th className="p-2 text-left">Close</th>
          <th className="p-2 text-left">Chart</th>
        </tr>
      </thead>
      <tbody>
        {tickers.map((t) => (
          <tr key={t} className="border-t">
            <td className="p-2 font-mono">{t}</td>
            <td className="p-2">{data[t]?.snapshot?.close ?? "-"}</td>
            <td className="p-2">
              <MiniChart symbol={t} />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}