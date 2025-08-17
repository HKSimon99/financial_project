"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";

export default function MiniChart({ symbol }: { symbol: string }) {
  const [points, setPoints] = useState<number[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const end = new Date();
        const start = new Date(end.getTime() - 30 * 24 * 60 * 60 * 1000);
        const s = start.toISOString().slice(0, 10);
        const e = end.toISOString().slice(0, 10);
        const data = await apiFetch<{ points: { close: number }[] }>(
          `/api/instrument/${symbol}/ohlcv?start=${s}&end=${e}`,
        );
        setPoints(data.points.map((p) => p.close));
      } catch {
        setPoints([]);
      }
    }
    load();
  }, [symbol]);

  if (!points.length) return <span className="text-gray-400">-</span>;

  const width = 80;
  const height = 30;
  const min = Math.min(...points);
  const max = Math.max(...points);
  const pts = points
    .map((p, i) => {
      const x = (i / (points.length - 1)) * width;
      const y = height - ((p - min) / (max - min || 1)) * height;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg width={width} height={height} className="text-blue-600">
      <polyline
        fill="none"
        stroke="currentColor"
        strokeWidth="1"
        points={pts}
      />
    </svg>
  );
}
