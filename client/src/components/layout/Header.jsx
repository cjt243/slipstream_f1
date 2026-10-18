import { Link } from "react-router-dom";
import { C, FONT } from "../../lib/tokens";
import { useRaces } from "../../hooks/useRaces";

/** Sticky top header: logo mark, wordmark, next-race indicator
 * (green while team changes are open, red during lockdown). */
export default function Header() {
  const { races, nextRaceId } = useRaces();
  const next = races.find((r) => r.id === nextRaceId);
  const locked = next?.status === "lockdown";
  const dot = locked ? C.danger : C.apex;
  return (
    <div
      className="sticky top-0 z-40 px-4 py-3 flex items-center justify-between"
      style={{
        background: `${C.cockpit}EE`,
        borderBottom: `1px solid ${C.border}`,
        backdropFilter: "blur(12px)",
      }}
    >
      <div className="flex items-center gap-2">
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
          style={{ fontSize: 14, fontFamily: FONT.display, color: C.white, letterSpacing: "0.15em" }}
        >
          SLIPSTREAM
        </span>
      </div>
      {next && (
        <Link to={`/race/${next.id}`} className="flex items-center gap-2" style={{ textDecoration: "none" }}>
          <div className="w-2 h-2 rounded-full" style={{ background: dot, boxShadow: `0 0 8px ${dot}` }} />
          <span style={{ fontSize: 12, color: C.muted, fontFamily: FONT.mono, letterSpacing: "0.06em" }}>
            R{next.round} · {locked ? "LOCKED" : (next.circuit || "").toUpperCase()}
          </span>
        </Link>
      )}
    </div>
  );
}
