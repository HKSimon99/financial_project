"use client";

import { Button } from "@/components/ui/button";
import { useWatchlistStore } from "@/lib/watchlist";

export default function Actions({ slug }: { slug: string }) {
  const { items, add, remove } = useWatchlistStore();
  const watching = items.includes(slug);
  const url = typeof window !== "undefined" ? window.location.href : "";

  const toggleWatch = () => {
    if (watching) remove(slug);
    else add(slug);
  };

  const share = async () => {
    try {
      if (navigator.share) await navigator.share({ url });
      else await navigator.clipboard.writeText(url);
    } catch {
      /* ignore */
    }
  };

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(url);
    } catch {
      /* ignore */
    }
  };

  return (
    <div className="flex gap-2">
      <Button onClick={toggleWatch}>{watching ? "Unwatch" : "Watch"}</Button>
      <Button onClick={share}>Share</Button>
      <Button onClick={copy}>Copy Link</Button>
    </div>
  );
}