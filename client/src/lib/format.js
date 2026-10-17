// Money is integer whole pounds (see docs/api-contracts.md). Format for display.
export function formatGBP(pounds) {
  if (pounds == null) return "—";
  return `£${(pounds / 1_000_000).toFixed(1)}M`;
}
