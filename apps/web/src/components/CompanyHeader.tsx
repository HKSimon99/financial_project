import { useEffect, useState } from "react";
import { api } from "../api/client";

export function CompanyHeader({ stock }: { stock: string }) {
  const [info, setInfo] = useState<any>(null);
  const [logo, setLogo] = useState<string | null>(null);
  useEffect(() => {
    (async () => {
      const r = await api.get(`/lookup/company/${stock}`);
      setInfo(r.data);
      const l = await api.get(`/lookup/logo/${stock}`);
      setLogo(l.data.logo_url || null);
    })();
  }, [stock]);
  if (!info) return null;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
      {logo && <img src={logo} width={60} height={60} style={{ objectFit: "contain" }} />}
      <h3 style={{ margin: 0 }}>{info.corp_name} ({info.stock_code})</h3>
    </div>
  );
}