export function RatioTable({ rows }: { rows: any[] }) {
  if (!rows?.length) return null;
  const cols = Object.keys(rows[0]).filter(k=>k!=="결산년월");
  return (
    <table style={{ width: "100%", borderCollapse: "collapse" }}>
      <thead>
        <tr>
          <th style={{ textAlign: "left", padding: 8 }}>결산년월</th>
          {cols.map(c=> <th key={c} style={{ textAlign: "right", padding: 8 }}>{c}</th>)}
        </tr>
      </thead>
      <tbody>
        {rows.map((r,i)=> (
          <tr key={i}>
            <td style={{ padding: 8 }}>{r["결산년월"]}</td>
            {cols.map(c=> <td key={c} style={{ textAlign: "right", padding: 8 }}>{Number(r[c]??0).toLocaleString()}</td>)}
          </tr>
        ))}
      </tbody>
    </table>
  );
}