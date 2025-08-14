import { useEffect, useState } from "react";
import { api } from "../api/client";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

export function PriceChart({ stock, start, end }: { stock: string; start: string; end: string }) {
  const [rows, setRows] = useState<any[]>([]);
  useEffect(()=>{ (async()=>{
    const r = await api.get(`/market/prices/${stock}`, { params: { start_date: start, end_date: end } });
    setRows(r.data.points.map((p:any)=>({ date:p.date, close:Number(p.close), volume:Number(p.volume||0) })));
  })(); }, [stock,start,end]);
  return (
    <div style={{ height: 320 }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={rows}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" minTickGap={24} />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="close" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}