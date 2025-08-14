import { useState } from "react";
import { api } from "../api/client";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from "recharts";

type CurvePoint = { date: string; value: number };

type OptimizeV1 = { tickers: string[]; weights: Record<string, number>; mean: number; vol: number; sharpe?: number };
type OptimizeV2 = { weights: number[]; annual_return: number; annual_volatility: number; sharpe_ratio: number; success: boolean };
type OptimizeOut = OptimizeV1 | OptimizeV2;

export default function Portfolio() {
  const [tickers, setTickers] = useState("005930, 000660, 035420");
  const [start, setStart] = useState("2024-01-01");
  const [end, setEnd] = useState("2025-08-01");
  const [method, setMethod] = useState<"sharpe" | "minvar">("sharpe");
  const [result, setResult] = useState<OptimizeOut | null>(null);
  const [curve, setCurve] = useState<CurvePoint[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const parseTickers = () => tickers.split(",").map(s => s.trim()).filter(Boolean);

  // Normalize weights to a vector aligned with current tickers
  const toWeightVector = (tick: string[], res: OptimizeOut | null): number[] => {
    if (!res) return new Array(tick.length).fill(1 / tick.length);
    if ("weights" in res && Array.isArray((res as any).weights)) {
      // V2: already an array
      return (res as OptimizeV2).weights.map(Number);
    }
    // V1: map ticker→weight object to array by order
    const map = (res as OptimizeV1).weights || {};
    return tick.map(t => Number(map[t] ?? 0));
  };

  const run = async () => {
    setLoading(true); setErr(null); setCurve(null);
    try {
      const body: any = {
        tickers: parseTickers(),
        start_date: start,
        end_date: end,
        risk_free: 0.02,
      };
      // 만약 백엔드 OptimizeIn에 method가 있으면 포함, 없으면 무시돼도 무해
      body.method = method;

      const r = await api.post("/portfolio/optimize", body);
      setResult(r.data as OptimizeOut);
    } catch (e: any) {
      setErr(e?.response?.data?.detail ?? e.message ?? "optimize failed");
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const backtest = async () => {
    setLoading(true); setErr(null);
    try {
      const tick = parseTickers();
      const weights = toWeightVector(tick, result);
      const r = await api.post("/portfolio/backtest", {
        tickers: tick,
        start_date: start,
        end_date: end,
        weights,
      });
      setCurve(r.data.curve as CurvePoint[]);
    } catch (e: any) {
      setErr(e?.response?.data?.detail ?? e.message ?? "backtest failed");
      setCurve(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div style={{ padding: 24 }}>
        <h2>포트폴리오 최적화</h2>
        <div style={{ display: "grid", gap: 8, gridTemplateColumns: "repeat(2, minmax(240px, 1fr))" }}>
          <input value={tickers} onChange={e=>setTickers(e.target.value)} placeholder="005930, 000660, 035420" />
          <select value={method} onChange={e=>setMethod(e.target.value as any)}>
            <option value="sharpe">Max Sharpe</option>
            <option value="minvar">Min Variance</option>
          </select>
          <input type="date" value={start} onChange={e=>setStart(e.target.value)} />
          <input type="date" value={end} onChange={e=>setEnd(e.target.value)} />
          <button onClick={run} disabled={loading}>최적화</button>
          <button onClick={backtest} disabled={!result || loading}>백테스트</button>
        </div>

        {err && <div style={{ marginTop: 12, color: "#c33" }}>{err}</div>}

        {result && (
          <pre style={{ marginTop: 16, background: "#111", color: "#0f0", padding: 12 }}>
            {JSON.stringify(result, null, 2)}
          </pre>
        )}
      </div>

      {curve && (
        <div style={{ padding: 24 }}>
          <div style={{ height: 360, marginTop: 16 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={curve}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" minTickGap={24} />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="value" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </>
  );
}
