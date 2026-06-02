import { C, FONT } from "../../lib/tokens";
import Mono from "./Mono";

/** Left label + right value row, with optional step badge and divider. */
export default function StatRow({ label, value, color = C.white, divider = true, step }) {
  return (
    <div
      className="flex items-center justify-between py-2"
      style={{ borderBottom: divider ? `1px solid ${C.border}` : "none" }}
    >
      <div className="flex items-center gap-2">
        {step != null && (
          <div
            className="w-5 h-5 rounded-full flex items-center justify-center"
            style={{ fontSize: 11, background: C.panel, color: C.ghost, fontFamily: FONT.mono, flexShrink: 0 }}
          >
            {step}
          </div>
        )}
        <span style={{ fontSize: 13, color: C.muted, fontFamily: FONT.body }}>{label}</span>
      </div>
      <Mono color={color} size="text-sm">
        {value}
      </Mono>
    </div>
  );
}
