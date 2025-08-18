"use client";

import { useEffect } from "react";
import { telemetry } from "../lib/telemetry";

export default function ConfidenceBadge({
  confidence,
}: {
  confidence: number;
}) {
  useEffect(() => {
    telemetry("ui.field_shown", { field: "confidence" });
  }, []);

  return (
    <span className="inline-block rounded bg-gray-200 px-2 py-1 text-xs">
      {confidence}
    </span>
  );
}
