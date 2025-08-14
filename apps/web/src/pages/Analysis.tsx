import { useState } from "react";
import { api } from "../api/client";
import type { PriceSeries } from "../api/types";

export default function Analysis() {
  const [corpCode, setCorpCode] = useState("00126380"); // 삼성전자 예시 DART corp_code
  const [year, setYear] = useState("2024");
  const [fsRows, setFsRows] = useState<any[]>([]);
  const [health, setHealth] = useState<any | null>(null);
  const [ratios, setRatios] = useState<any | null>(null);

  const loadFS = async () => {
    // Example: if you already fetched FS via API/market → adapt accordingly
    // Here we assume you have an endpoint that returns FinancialStatement.rows
    const r = await api.get(`/financials/${corpCode}`, { params: { year } });
    setFsRows(r.data.rows);
  };

  const calcHealth = async () => {
    const r = await api.post(`/analysis/financial-health`, fsRows);
    setHealth(r.data);
  };

  const calcRatios = async () => {
    // Need prices; reuse /market/prices
    const prices = await api.get<PriceSeries>(`/market/prices/005930`, { params: { start_date: `${year}-01-01`, end_date: `${year}-12-31` } });
    const compact = prices.data.points.map(p => ({ date: p.date, close: p.close }));
    const r = await api.post(`/analysis/ratios`, fsRows, { params: {} , headers: {}, data: undefined});
  };

  return (
    <div style={{ padding: 24 }}>
      <h2>재무 분석</h2>
      <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        <input value={corpCode} onChange={e=>setCorpCode(e.target.value)} placeholder="DART corp_code" />
        <input value={year} onChange={e=>setYear(e.target.value)} placeholder="Year" />
        <button onClick={loadFS}>FS 불러오기</button>
        <button onClick={calcHealth} disabled={!fsRows.length}>건전성 계산</button>
      </div>
      {health && (
        <pre style={{ background: "#111", color: "#0f0", padding: 12 }}>{JSON.stringify(health, null, 2)}</pre>
      )}
    </div>
  );
}