import dynamic from "next/dynamic";
import Actions from "./actions";
import ConfidenceBadge from "@/components/confidence-badge";

const Chart = dynamic(() => import("@/components/chart"), { ssr: false });

// Domain types for this page
type Snapshot = unknown; // you only pretty-print it
type Fundamentals = unknown;
type NewsItem = { id: string | number; url: string; title: string };
type WhyMoving = { confidence?: number } & Record<string, unknown>;

export default async function InstrumentPage({
  params,
}: {
  params: { slug: string };
}) {
  const { slug } = params;

  async function fetchJSON<T>(url: string): Promise<T | null> {
    try {
      const res = await fetch(url, { next: { revalidate: 0 } });
      if (!res.ok) return null;
      return (await res.json()) as T;
    } catch {
      return null;
    }
  }

  const [snapshot, fundamentals, news, whyMoving] = await Promise.all([
    fetchJSON<Snapshot>(`/api/instrument/${slug}/snapshot`),
    fetchJSON<Fundamentals>(`/api/instrument/${slug}/metrics`),
    fetchJSON<NewsItem[]>(`/api/instrument/${slug}/news`),
    fetchJSON<WhyMoving>(`/api/why-moving/${slug}`),
  ]);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{slug.toUpperCase()}</h1>
      <Actions slug={slug} />
      <Chart slug={slug} />

      <section>
        <h2 className="text-xl font-semibold">Snapshot</h2>
        <pre className="text-sm bg-gray-100 p-2 rounded">
          {JSON.stringify(snapshot, null, 2)}
        </pre>
      </section>

      <section>
        <h2 className="text-xl font-semibold">Fundamentals</h2>
        <pre className="text-sm bg-gray-100 p-2 rounded">
          {JSON.stringify(fundamentals, null, 2)}
        </pre>
      </section>

      <section>
        <h2 className="text-xl font-semibold">News</h2>
        {(news?.length ?? 0) > 0 ? (
          <ul className="list-disc ml-5 space-y-1">
            {news!.map((n: NewsItem) => (
              <li key={n.id}>
                <a href={n.url} target="_blank" rel="noopener noreferrer">
                  {n.title}
                </a>
              </li>
            ))}
          </ul>
        ) : (
          <p>No recent news</p>
        )}
      </section>

      <section>
        <a
          href={`/compare?symbols=${encodeURIComponent(slug)}`}
          className="text-blue-500 underline"
        >
          Compare with other instruments
        </a>
      </section>

      <section>
        <h2 className="text-xl font-semibold">Why Moving</h2>
        {whyMoving?.confidence != null && (
          <p>Confidence: {(whyMoving.confidence * 100).toFixed(0)}%</p>
        )}
        {whyMoving ? (
          <div className="space-y-2">
            {whyMoving.confidence != null && (
              <ConfidenceBadge confidence={whyMoving.confidence} />
            )}
            <pre className="text-sm bg-gray-100 p-2 rounded">
              {JSON.stringify(whyMoving, null, 2)}
            </pre>
          </div>
        ) : (
          <p>No data</p>
        )}
      </section>
    </div>
  );
}
