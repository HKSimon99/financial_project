import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import { CompanyHeader } from "../components/CompanyHeader";
import { PriceChart } from "../components/PriceChart";
import { FinancialBars } from "../components/FinancialBars";
import { RatioTable } from "../components/RatioTable";
import { CandleChart } from "../components/CandleChart";

// Minimal shapes we rely on
type CompanyInfo = { corp_name: string; corp_code: string; stock_code: string };

type Opinion = { opinion?: string | null; target_price?: number; analyst_count?: number };

export type FinancialRow = {
  account_nm: string;
  thstrm_amount?: number | string | null;
  [key: string]: unknown;
};

export type RatioRow = { [key: string]: number | string | undefined };

export default function Company() {
  const [stock, setStock] = useState("005930");
  const [start, setStart] = useState("2024-01-01");
  const [end, setEnd] = useState("2025-08-01");
  const [year, setYear] = useState<number>(2024);

  // Server data
  const [info, setInfo] = useState<CompanyInfo | null>(null);
  const [fsRows, setFsRows] = useState<FinancialRow[]>([]);
  const [ratios, setRatios] = useState<RatioRow[]>([]);
  const [opinion, setOpinion] = useState<Opinion | null>(null);
  const [logo, setLogo] = useState<string | null>(null);
  const [lastPrice, setLastPrice] = useState<number | null>(null);

  // UX state
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const canBacktestRange = useMemo(() => start <= end, [start, end]);

  const loadAll = useCallback(async () => {
    setLoading(true);
    setErr(null);
    try {
      // 1) Company info (corp_code)
      const ci = await api.get(`/lookup/company/${stock}`);
      setInfo(ci.data);

      // 2) Parallel: financials snapshot, ratios, opinion, logo, prices
      const corp = ci.data.corp_code;
      const [fin, rat, op, lg, prices] = await Promise.all([
        api
          .get(`/market/financials/${corp}`, { params: { year } })
          .catch(() => ({ data: { rows: [] } })),
        api.get(`/market/ratios/${stock}`).catch(() => ({ data: { rows: [] } })),
        api.get(`/market/opinion/${stock}`).catch(() => ({ data: {} })),
        api.get(`/lookup/logo/${stock}`).catch(() => ({ data: { logo_url: null } })),
        api
          .get(`/market/prices/${stock}`, { params: { start_date: start, end_date: end } })
          .catch(() => ({ data: { points: [] } })),
      ]);

      const rows = fin.data?.rows || fin.data?.list || [];
      setFsRows(Array.isArray(rows) ? rows : []);
      setRatios(Array.isArray(rat.data?.rows) ? rat.data.rows : []);
      setOpinion(op.data || {});
      setLogo(lg.data?.logo_url || null);
      const pts = Array.isArray(prices.data?.points) ? prices.data.points : [];
      const lp = pts.length ? Number(pts[pts.length - 1]?.close) : null;
      setLastPrice(lp);
    } catch (e) {
      const errObj = e as { response?: { data?: { detail?: string } }; message?: string };
      setErr(errObj.response?.data?.detail ?? errObj.message ?? "load failed");
      setFsRows([]);
      setRatios([]);
      setOpinion(null);
      setLogo(null);
      setLastPrice(null);
    } finally {
      setLoading(false);
    }
  }, [stock, start, end, year]);

  // Auto-load on first mount and when stock/year changes
  useEffect(() => {
    loadAll();
  }, [loadAll]);

  return (
    <div className="p-6 grid gap-4">
      <h2 className="m-0">단일 기업 분석</h2>

      {/* Controls */}
      <div className="grid gap-2 [grid-template-columns:repeat(3,minmax(220px,1fr))]">
        <input value={stock} onChange={(e)=>setStock(e.target.value)} placeholder="종목코드 (예: 005930)" />
        <div className="flex gap-2">
          <input type="date" value={start} onChange={(e)=>setStart(e.target.value)} />
          <input type="date" value={end} onChange={(e)=>setEnd(e.target.value)} />
        </div>
        <div className="flex gap-2 items-center">
          <label>연도</label>
          <input type="number" value={year} onChange={(e)=>setYear(parseInt(e.target.value||"0",10)||year)} style={{ width: 120 }} />
          <button onClick={loadAll} disabled={loading}>불러오기</button>
        </div>
      </div>

      {err && <div className="text-danger">{err}</div>}

      {/* Company Header (logo + name + price) */}
      <CompanyHeader info={info} logo={logo} price={lastPrice} />

      {/* Price line chart (component fetches its own data) */}
      <div>
        <h3 style={{ margin: "8px 0" }}>주가</h3>
        <PriceChart stock={stock} start={start} end={end} />
        <CandleChart stock={stock} start={start} end={end} />
        {!canBacktestRange && (
          <div className="text-[#c33] mt-1">시작일이 종료일보다 이후일 수 없습니다.</div>
        )}
      </div>

      {/* Financial snapshot bars */}
      <div>
        <h3 style={{ margin: "8px 0" }}>재무제표 주요 지표 ({year})</h3>
        {fsRows?.length ? (
          <FinancialBars rows={fsRows} />
        ) : (
          <div style={{ opacity: 0.7 }}>데이터가 없습니다.</div>
        )}
      </div>

      {/* Ratios table */}
      <div>
        <h3 style={{ margin: "8px 0" }}>재무비율</h3>
        {ratios?.length ? (
          <RatioTable rows={ratios} />
        ) : (
          <div style={{ opacity: 0.7 }}>데이터가 없습니다.</div>
        )}
      </div>

      {/* Investment opinion (optional) */}
      <div>
        <h3 style={{ margin: "8px 0" }}>투자의견</h3>
        {opinion ? (
          <div className="flex gap-4 flex-wrap">
            <Chip label={`의견: ${opinion.opinion ?? "-"}`} />
            <Chip label={`목표가: ${opinion.target_price ? opinion.target_price.toLocaleString() : "-"}`} />
            <Chip label={`애널리스트 수: ${opinion.analyst_count ?? 0}`} />
          </div>
        ) : (
          <div style={{ opacity: 0.7 }}>데이터가 없습니다.</div>
        )}
      </div>
    </div>
  );
}

function Chip({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center px-2.5 py-1 rounded-full border border-gray-700 bg-gray-900 text-sm">
      {label}
    </span>
  );
}