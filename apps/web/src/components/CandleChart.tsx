import { useEffect, useRef } from "react";
import { createChart, ColorType, CrosshairMode, IChartApi, DeepPartial, ChartOptions, Time } from "lightweight-charts";
import { api } from "../api/client";

/**
 * Candlestick chart component backed by /market/prices endpoint.
 *
 * Usage:
 * <CandleChart stock="005930" start="2024-01-01" end="2025-08-01" />
 */
export function CandleChart({ stock, start, end }: { stock: string; start: string; end: string }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);

  // Create chart once
  useEffect(() => {
    if (!containerRef.current || chartRef.current) return;

    const opts: DeepPartial<ChartOptions> = {
      layout: {
        background: { type: ColorType.Solid, color: "#0b0b0c" },
        textColor: "#d0d0d0",
      },
      grid: {
        vertLines: { color: "#1e1e22" },
        horzLines: { color: "#1e1e22" },
      },
      crosshair: { mode: CrosshairMode.Normal },
      timeScale: { rightOffset: 4, barSpacing: 8, fixLeftEdge: true, fixRightEdge: false, timeVisible: true, secondsVisible: false },
      rightPriceScale: { borderVisible: false },
      localization: { priceFormatter: (p: number) => p.toLocaleString() },
    };

    const chart = createChart(containerRef.current, { width: containerRef.current.clientWidth, height: 360, ...opts });
    chart.addCandlestickSeries({
      upColor: "#26a69a",
      downColor: "#ef5350",
      borderDownColor: "#ef5350",
      borderUpColor: "#26a69a",
      wickDownColor: "#ef5350",
      wickUpColor: "#26a69a",
    });
    chart.addHistogramSeries({
      priceFormat: { type: "volume" },
      priceScaleId: "left",
      base: 0,
      color: "#3a3f5a",
    });
    chart.priceScale('left').applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } });

    // Resize observer for responsiveness
    const ro = new ResizeObserver(() => {
      if (!containerRef.current) return;
      chart.applyOptions({ width: containerRef.current.clientWidth });
    });
    ro.observe(containerRef.current);

    chartRef.current = chart;
    return () => {
      ro.disconnect();
      chart.remove();
      chartRef.current = null;
    };
  }, []);

  // Reload data when inputs change (stock/start/end)
  useEffect(() => {
    if (!chartRef.current) return;
    (async () => {
      try {
        const r = await api.get(`/market/prices/${stock}`, {
          params: { start_date: start, end_date: end },
        });
        const rows: Array<{ date: string; open?: number; high?: number; low?: number; close?: number; volume?: number }> =
          r.data.points || [];
        const candles = rows
          .filter((d) => d.open != null && d.high != null && d.low != null && d.close != null)
          .map((d) => ({
            time: d.date as unknown as Time,
            open: Number(d.open),
            high: Number(d.high),
            low: Number(d.low),
            close: Number(d.close),
          }));
        const volumes = rows.map((d) => ({
          time: d.date as unknown as Time,
          value: Number(d.volume || 0),
          color: d.close != null && d.open != null && Number(d.close) >= Number(d.open) ? "#2e7d32" : "#c62828",
        }));

        // Find series (first is candle, second is volume)
        type ChartWithSeries = IChartApi & { serieses?: () => unknown[] };
        const series = (chartRef.current as ChartWithSeries).serieses?.();
        const candleSeries = series?.[0] as { setData: (d: typeof candles) => void } | undefined;
        const volumeSeries = series?.[1] as { setData: (d: typeof volumes) => void } | undefined;
        if (candleSeries && volumeSeries) {
          candleSeries.setData(candles);
          volumeSeries.setData(volumes);
          chartRef.current.timeScale().fitContent();
        }
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