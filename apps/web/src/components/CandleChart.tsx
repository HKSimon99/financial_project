import { useEffect, useRef } from "react";
import {
  createChart,
  ColorType,
  CrosshairMode,
  CandlestickSeries,
  HistogramSeries,
} from "lightweight-charts";
import type {
  IChartApi,
  ISeriesApi,
  DeepPartial,
  ChartOptions,
  Time,
} from "lightweight-charts";
import { api } from "../api/client";

export function CandleChart({
  stock, start, end,
}: { stock: string; start: string; end: string }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick", Time> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram", Time> | null>(null);

  useEffect(() => {
    if (!containerRef.current || chartRef.current) return;

    const opts: DeepPartial<ChartOptions> = {
      layout: {
        background: { type: ColorType.Solid, color: "#0b0b0c" },
        textColor: "#d0d0d0",
      },
      grid: { vertLines: { color: "#1e1e22" }, horzLines: { color: "#1e1e22" } },
      crosshair: { mode: CrosshairMode.Normal },
      timeScale: { rightOffset: 4, barSpacing: 8, fixLeftEdge: true, timeVisible: true, secondsVisible: false },
      rightPriceScale: { borderVisible: false },
      localization: { priceFormatter: (p: number) => p.toLocaleString() },
    };

    const el = containerRef.current;
    const chart = createChart(el, { width: el.clientWidth, height: 360, ...opts });

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#26a69a",
      downColor: "#ef5350",
      borderDownColor: "#ef5350",
      borderUpColor: "#26a69a",
      wickDownColor: "#ef5350",
      wickUpColor: "#26a69a",
    });

    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" },
      priceScaleId: "left",
      base: 0,
      color: "#3a3f5a",
    });

    chart.priceScale("left").applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    volumeSeriesRef.current = volumeSeries;

    const ro = new ResizeObserver(() => {
      if (!containerRef.current) return;
      chart.applyOptions({ width: containerRef.current.clientWidth });
    });
    ro.observe(el);

    return () => {
      ro.disconnect();
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      volumeSeriesRef.current = null;
    };
  }, []);

  useEffect(() => {
    const chart = chartRef.current;
    const candleSeries = candleSeriesRef.current;
    const volumeSeries = volumeSeriesRef.current;
    if (!chart || !candleSeries || !volumeSeries) return;

    (async () => {
      try {
        const r = await api.get(`/market/prices/${stock}`, { params: { start_date: start, end_date: end } });
        const rows: Array<{ date: string; open?: number; high?: number; low?: number; close?: number; volume?: number }> =
          r.data?.points ?? [];

        const candles = rows
          .filter(d => d.open != null && d.high != null && d.low != null && d.close != null)
          .map(d => ({
            time: d.date as unknown as Time, // 'YYYY-MM-DD' is valid BusinessDay string
            open: Number(d.open), high: Number(d.high), low: Number(d.low), close: Number(d.close),
          }));

        const volumes = rows.map(d => ({
          time: d.date as unknown as Time,
          value: Number(d.volume ?? 0),
          color: d.close != null && d.open != null && Number(d.close) >= Number(d.open) ? "#2e7d32" : "#c62828",
        }));

        candleSeries.setData(candles);
        volumeSeries.setData(volumes);
        chart.timeScale().fitContent();
      } catch (e) {
        console.error("Failed to reload prices", e);
      }
    })();
  }, [stock, start, end]);

  return (
    <div>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 8 }}>
        <h4 style={{ margin: 0 }}>캔들 차트</h4>
        <small style={{ opacity: 0.7 }}>{stock} • {start} → {end}</small>
      </div>
      <div ref={containerRef} style={{ width: "100%", height: 360 }} />
    </div>
  );
}
