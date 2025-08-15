export type CompanyInfo = {
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
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 16,
        padding: "12px 16px",
        borderRadius: 12,
        background: "linear-gradient(90deg, var(--color-primary), var(--color-secondary))",
        color: "#fff",
      }}
    >
      {logo && (
        <img
          src={logo}
          width={60}
          height={60}
          style={{ objectFit: "contain", borderRadius: 8 }}
        />
      )}
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
        padding: "4px 10px",
        borderRadius: 999,
        border: "1px solid #444",
        background: "#111",
        fontSize: 13,
      }}
    >
      {label}
    </span>
  );
}