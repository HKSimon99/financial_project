"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import { Button } from "../../src/components/ui/button";
import { Input } from "../../src/components/ui/input";

interface Rule {
  metric: string;
  op: string;
  value: number;
}

export default function ScreenersPage() {
  const [rules, setRules] = useState<Rule[]>([{ metric: "pe", op: "<", value: 15 }]);
  const [results, setResults] = useState<any[]>([]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const encoded = params.get("rules");
    if (encoded) {
      try {
        const parsed = JSON.parse(decodeURIComponent(encoded));
        setRules(parsed);
      } catch {
        /* ignore */
      }
    }
  }, []);

  const updateRule = (idx: number, patch: Partial<Rule>) => {
    setRules((r) => r.map((rule, i) => (i === idx ? { ...rule, ...patch } : rule)));
  };

  const addRule = () => setRules([...rules, { metric: "pe", op: "<", value: 0 }]);
  const removeRule = (idx: number) => setRules(rules.filter((_, i) => i !== idx));

  const run = async () => {
    const res = await apiFetch<any[]>("/api/screeners/run", {
      method: "POST",
      body: JSON.stringify({ rules }),
    });
    setResults(res);
  };

  const share = () => {
    const encoded = encodeURIComponent(JSON.stringify(rules));
    const url = `${window.location.origin}/screeners?rules=${encoded}`;
    navigator.clipboard.writeText(url);
    alert("Shareable link copied to clipboard");
  };

  const exportCsv = () => {
    const header = "ticker,name\n";
    const rows = results.map((r) => `${r.ticker},${r.name}`).join("\n");
    const blob = new Blob([header + rows], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "screener.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-xl font-bold">Screeners</h1>
      <div className="space-y-2">
        {rules.map((r, i) => (
          <div key={i} className="flex gap-2 items-center">
            <Input
              value={r.metric}
              onChange={(e) => updateRule(i, { metric: e.target.value })}
              className="w-32"
            />
            <select
              value={r.op}
              onChange={(e) => updateRule(i, { op: e.target.value })}
              className="border rounded p-2"
            >
              {['<', '<=', '>', '>=', '=='].map((op) => (
                <option key={op} value={op}>
                  {op}
                </option>
              ))}
            </select>
            <Input
              type="number"
              value={r.value}
              onChange={(e) => updateRule(i, { value: parseFloat(e.target.value) })}
              className="w-24"
            />
            <Button variant="secondary" onClick={() => removeRule(i)}>
              Remove
            </Button>
          </div>
        ))}
        <Button onClick={addRule}>Add Rule</Button>
      </div>
      <div className="flex gap-2">
        <Button onClick={run}>Run</Button>
        <Button variant="secondary" onClick={share}>
          Share
        </Button>
        <Button variant="secondary" onClick={exportCsv} disabled={!results.length}>
          Export CSV
        </Button>
      </div>
      <ul className="space-y-2">
        {results.map((r) => (
          <li key={r.ticker} className="border p-2">
            {r.ticker} - {r.name}
          </li>
        ))}
      </ul>
    </div>
  );
}