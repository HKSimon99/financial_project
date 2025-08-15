type CompanyInfo = {
  corp_name: string;
  corp_code: string;
  stock_code: string;
};

export function CompanyHeader({
  info,
  logo,
  price,
}: {
  info: CompanyInfo | null;
  logo: string | null;
  price: number | null;
}) {
  if (!info) return null;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
      {logo && <img src={logo} width={60} height={60} style={{ objectFit: "contain" }} />}
      <h3 style={{ margin: 0, display: "flex", alignItems: "center", gap: 12 }}>
        {info.corp_name} ({info.stock_code})
        {price != null && <Chip label={`현재가: ${price.toLocaleString()}`} />}
      </h3>
    </div>
  );
}

function Chip({ label }: { label: string }) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding: "2px 8px",
        borderRadius: 999,
        border: "1px solid #444",
        background: "#111",
        fontSize: 12,
      }}
    >
      {label}
    </span>
  );
}

