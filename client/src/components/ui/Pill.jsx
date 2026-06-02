import { C, FONT } from "../../lib/tokens";

/** Compact colored tag. */
export default function Pill({ label, color = C.muted }) {
  return (
    <span
      className="font-bold tracking-wider px-2 py-0.5 rounded"
      style={{ fontSize: 11, background: `${color}20`, color, border: `1px solid ${color}40`, fontFamily: FONT.mono }}
    >
      {label}
    </span>
  );
}
