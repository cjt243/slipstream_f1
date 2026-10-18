import { C, FONT } from "../../lib/tokens";

/** Mono uppercase button. `tone` picks the accent; `solid` fills it. */
export default function Button({ children, onClick, disabled, tone = C.speed, solid = false, full = false, type = "button" }) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`px-4 py-2.5 rounded tracking-widest uppercase ${full ? "w-full" : ""}`}
      style={{
        fontSize: 12,
        fontFamily: FONT.mono,
        fontWeight: 700,
        background: solid ? tone : `${tone}15`,
        color: solid ? C.void : tone,
        border: `1px solid ${tone}60`,
        opacity: disabled ? 0.4 : 1,
        cursor: disabled ? "not-allowed" : "pointer",
      }}
    >
      {children}
    </button>
  );
}
