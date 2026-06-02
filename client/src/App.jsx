import { useEffect, useState } from "react";
import { C, FONT } from "./lib/tokens";
import { api } from "./lib/api";
import { Card, Label, Pill, Mono, StatRow } from "./components/ui";

// Tier 0 placeholder. Confirms the design system renders and the API wrapper
// can reach the backend. Real routing/pages arrive in issue 1C.
export default function App() {
  const [health, setHealth] = useState({ state: "loading", value: null });

  useEffect(() => {
    api
      .get("/health", { auth: false })
      .then((data) => setHealth({ state: "ok", value: data?.status ?? "ok" }))
      .catch((err) => setHealth({ state: "error", value: err.message }));
  }, []);

  const healthColor =
    health.state === "ok" ? C.apex : health.state === "error" ? C.danger : C.muted;

  return (
    <div className="min-h-screen w-full" style={{ background: C.void, color: C.white, fontFamily: FONT.body }}>
      <div className="px-4 pb-20 pt-8 max-w-2xl mx-auto">
        <div className="flex items-center gap-2 mb-6">
          <div
            className="w-7 h-7 flex items-center justify-center font-bold"
            style={{
              fontSize: 12,
              fontFamily: FONT.mono,
              background: `linear-gradient(135deg, ${C.speed}, ${C.speed}60)`,
              color: C.void,
              clipPath: "polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)",
            }}
          >
            S
          </div>
          <span
            className="tracking-widest"
            style={{ fontSize: 16, fontFamily: FONT.display, color: C.white, letterSpacing: "0.15em" }}
          >
            SLIPSTREAM
          </span>
          <Pill label="TIER 0" color={C.speed} />
        </div>

        <Label>Scaffold Status</Label>
        <Card accent={healthColor}>
          <StatRow label="Frontend" value="rendering" color={C.apex} />
          <StatRow
            label="Backend /api/health"
            value={health.state === "loading" ? "checking…" : health.value}
            color={healthColor}
            divider={false}
          />
        </Card>

        <div style={{ fontSize: 13, color: C.ghost, fontFamily: FONT.body }}>
          Design tokens, shared UI components, and the API wrapper are wired up.
          Routing and pages land in issue 1C. <Mono color={C.muted}>v0.1.0</Mono>
        </div>
      </div>
    </div>
  );
}
