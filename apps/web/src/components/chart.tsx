"use client";

import { useEffect, useState } from "react";

interface PricePoint {
  timestamp?: string;
  open?: number;
  high?: number;
  low?: number;
  close?: number;
  volume?: number;
  [key: string]: any;
}

export default function Chart({ slug }: { slug: string }) {
  const [points, setPoints] = useState<PricePoint[]>([]);

  useEffect(() => {
    let es: EventSource | null = null;
    let timer: NodeJS.Timeout | null = null;

    const startPolling = () => {
      timer = setInterval(async () => {
        try {
          const now = new Date();
          const end = now.toISOString().slice(0, 10);
          const start = new Date(now.getTime() - 24 * 60 * 60 * 1000)
            .toISOString()
            .slice(0, 10);
          const res = await fetch(
            `/api/instrument/${slug}/ohlcv?start=${start}&end=${end}`,
          );
          const data = await res.json();
          if (data?.points) setPoints(data.points);
        } catch {
          /* ignore */
        }
      }, 5000);
    };

    if (typeof EventSource !== "undefined") {
      es = new EventSource(`/api/instrument/${slug}/ohlcv?live=true`);
      es.onmessage = (e) => {
        try {
          const point = JSON.parse(e.data);
          setPoints((prev) => [...prev, point].slice(-500));
        } catch {
          /* ignore */
        }
      };
      es.onerror = () => {
        es?.close();
        startPolling();
      };
    } else {
      startPolling();
    }

    return () => {
      es?.close();
      if (timer) clearInterval(timer);
    };
  }, [slug]);

  return (
    <pre className="text-xs bg-gray-100 p-2 rounded h-64 overflow-auto">
      {JSON.stringify(points, null, 2)}
    </pre>
  );
}
