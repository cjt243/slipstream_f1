import { C, FONT } from "../../lib/tokens";

/** Monospaced, tabular numeric value. */
export default function Mono({ children, color = C.white, size = "text-sm" }) {
  return (
    <span className={`${size} font-bold tabular-nums`} style={{ fontFamily: FONT.mono, color }}>
      {children}
    </span>
  );
}
