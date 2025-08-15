import { useEffect, useState } from "react";
import { api } from "../api/client";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

type PricePoint = { date: string; close: number; volume: number };
type RawPoint = { date: string; close?: number | string; volume?: number | string };

export function PriceChart({ stock, start, end }: { stock: string; start: string; end: string }) {
  const [rows, setRows] = useState<PricePoint[]>([]);
  useEffect(() => {
    (async () => {
      const r = await api.get(`/market/prices/${stock}`, {
        params: { start_date: start, end_date: end },
      });
      const mapped = (r.data.points as RawPoint[]).map((p) => ({
        date: p.date,
        close: Number(p.close ?? 0),
        volume: Number(p.volume ?? 0),
      }));
      setRows(mapped);
    })();
  }, [stock, start, end]);
  return (
    <div style={{ height: 320 }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={rows}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" minTickGap={24} />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="close" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}