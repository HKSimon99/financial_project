import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

export function FinancialBars({ rows }: { rows: any[] }) {
  const want = new Set(["매출액","영업이익","당기순이익","자산총계","부채총계","자본총계"]);
  const data = rows.filter(r => want.has(r.account_nm)).map(r => ({ name: r.account_nm, value: Number(r.thstrm_amount||0) }));
  return (
    <div style={{ height: 360 }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis tickFormatter={(v)=>v.toLocaleString()} />
          <Tooltip formatter={(v)=>Number(v).toLocaleString()} />
          <Bar dataKey="value" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}