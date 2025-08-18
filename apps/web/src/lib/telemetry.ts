export function telemetry(
  event: string,
  payload: Record<string, unknown> = {},
) {
  void fetch("/api/telemetry", {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify({ event, ...payload }),
    keepalive: true,
  }).catch(() => {
    /* ignore */
  });
}
