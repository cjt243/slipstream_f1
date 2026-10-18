// Money is integer whole pounds (see docs/api-contracts.md). Format for display.
export function formatGBP(pounds) {
  if (pounds == null) return "—";
  return `£${(pounds / 1_000_000).toFixed(1)}M`;
}

// Timestamps are ISO-8601 UTC; display in the viewer's local time.
export function formatDay(iso) {
  if (!iso) return "TBC";
  return new Date(iso).toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" });
}

export function formatDayTime(iso) {
  if (!iso) return "TBC";
  return new Date(iso).toLocaleString(undefined, {
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// "2d 04h 13m" / "04h 13m 09s" until `iso`, or null once it has passed.
export function formatCountdown(iso, now = Date.now()) {
  if (!iso) return null;
  const ms = new Date(iso).getTime() - now;
  if (ms <= 0) return null;
  const s = Math.floor(ms / 1000);
  const d = Math.floor(s / 86400);
  const h = String(Math.floor((s % 86400) / 3600)).padStart(2, "0");
  const m = String(Math.floor((s % 3600) / 60)).padStart(2, "0");
  const sec = String(s % 60).padStart(2, "0");
  return d > 0 ? `${d}d ${h}h ${m}m` : `${h}h ${m}m ${sec}s`;
}

// Signed salary movement, e.g. "▲ £0.4M" / "▼ £1.2M"; null when unchanged/unknown.
export function formatDelta(pounds) {
  if (!pounds) return null;
  return `${pounds > 0 ? "▲" : "▼"} £${(Math.abs(pounds) / 1_000_000).toFixed(1)}M`;
}
