import { useState } from "react";
import { api } from "../api/client";
import { Card } from "../components/ui/Card";

type FsRow = Record<string, unknown>;
type Health = Record<string, unknown>;

export default function Analysis() {
  const [corpCode, setCorpCode] = useState("00126380"); // 삼성전자 예시 DART corp_code
  const [year, setYear] = useState("2024");
  const [fsRows, setFsRows] = useState<FsRow[]>([]);
  const [health, setHealth] = useState<Health | null>(null);

  const loadFS = async () => {
    const r = await api.get(`/financials/${corpCode}`, { params: { year } });
    setFsRows(r.data.rows as FsRow[]);
  };

  const calcHealth = async () => {
    const r = await api.post(`/analysis/financial-health`, fsRows);
    setHealth(r.data as Health);
  };

  return (
    <Card title="재무 분석">
      <div className="flex gap-2 mb-3">
        <input
          value={corpCode}
          onChange={(e) => setCorpCode(e.target.value)}
          placeholder="DART corp_code"
          className="border rounded px-2 py-1"
        />
        <input
          value={year}
          onChange={(e) => setYear(e.target.value)}
          placeholder="Year"
          className="border rounded px-2 py-1"
        />
        <button
          onClick={loadFS}
          className="px-3 py-2 rounded-md bg-primary text-white hover:bg-secondary"
        >
          FS 불러오기
        </button>
        <button
          onClick={calcHealth}
          disabled={!fsRows.length}
          className="px-3 py-2 rounded-md bg-primary text-white hover:bg-secondary disabled:opacity-50"
        >
          건전성 계산
        </button>
      </div>
      {health && (
        <pre className="bg-gray-900 text-green-400 p-3 overflow-x-auto">
          {JSON.stringify(health, null, 2)}
        </pre>
      )}
    </Card>
  );
}