import dynamic from "next/dynamic";
import Actions from "./actions";

const Chart = dynamic(() => import("@/components/chart"), { ssr: false });

export default async function InstrumentPage({ params }: { params: { slug: string } }) {
  const { slug } = params;

  async function fetchJSON(url: string) {
    try {
      const res = await fetch(url, { next: { revalidate: 0 } });
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  }

  const [snapshot, fundamentals, news, whyMoving] = await Promise.all([
    fetchJSON(`/api/instrument/${slug}/snapshot`),
    fetchJSON(`/api/instrument/${slug}/metrics`),
    fetchJSON(`/api/instrument/${slug}/news`),
    fetchJSON(`/api/why-moving/${slug}`),
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
        {news?.length ? (
          <ul className="list-disc ml-5 space-y-1">
            {news.map((n: any) => (
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
        <pre className="text-sm bg-gray-100 p-2 rounded">
          {JSON.stringify(whyMoving, null, 2)}
        </pre>
      </section>
    </div>
  );
}