import { C, FONT } from "../../lib/tokens";

/** Section label with flanking gradient rules. */
export default function Label({ children }) {
  return (
    <div
      className="tracking-widest uppercase mb-4 flex items-center gap-3"
      style={{ color: C.speed, fontSize: 11, fontFamily: FONT.mono, letterSpacing: "0.15em" }}
    >
      <div className="h-px flex-1" style={{ background: `linear-gradient(to right, ${C.speed}50, transparent)` }} />
      {children}
      <div className="h-px flex-1" style={{ background: `linear-gradient(to left, ${C.speed}50, transparent)` }} />
    </div>
  );
}
