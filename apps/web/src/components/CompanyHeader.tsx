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
    <div className="flex items-center gap-4 p-3 rounded-xl bg-gradient-to-r from-primary to-secondary text-white">
      {logo && (
        <img src={logo} width={60} height={60} className="object-contain rounded-lg" />
      )}
      <h3 className="m-0 flex items-center gap-3">
        {info.corp_name} ({info.stock_code})
        {price != null && <Chip label={`현재가: ${price.toLocaleString()}`} />}
      </h3>
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