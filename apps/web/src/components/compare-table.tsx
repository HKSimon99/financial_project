"use client";

import { useEffect, useState, type ReactNode } from "react";
import MiniChart from "./mini-chart";
import { apiFetch } from "../../lib/api";
import { telemetry } from "../lib/telemetry";

interface SnapshotData {
  close?: number | null;
  change?: number | null;
  volume?: number | null;
}

interface Snapshot {
  slug: string;
  snapshot?: SnapshotData;
}

function Field({ value, field }: { value: ReactNode; field: string }) {
  useEffect(() => {
    telemetry("ui.field_shown", { field });
  }, [field]);

  return <>{value}</>;
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
          <th className="p-2 text-left">Change</th>
          <th className="p-2 text-left">Volume</th>
          <th className="p-2 text-left">Chart</th>
        </tr>
      </thead>
      <tbody>
        {tickers.map((t) => {
          return (
            <tr key={t} className="border-t">
              <td className="p-2 font-mono">{t}</td>
              <td className="p-2">{data[t]?.snapshot?.close ?? "-"}</td>
              <td className="p-2">
                {data[t]?.snapshot?.change != null ? (
                  <Field value={data[t].snapshot.change} field="change" />
                ) : (
                  "-"
                )}
              </td>
              <td className="p-2">
                {data[t]?.snapshot?.volume != null ? (
                  <Field value={data[t].snapshot.volume} field="volume" />
                ) : (
                  "-"
                )}
              </td>
              <td className="p-2">
                <MiniChart symbol={t} />
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
