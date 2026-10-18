import { C, FONT } from "../../lib/tokens";

export default function EmptySlot({ label, onClick, disabled }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="w-full p-4 rounded-lg mb-3 text-left"
      style={{
        background: "transparent",
        border: `1px dashed ${disabled ? C.border : C.speed + "60"}`,
        color: disabled ? C.ghost : C.speed,
        fontFamily: FONT.mono,
        fontSize: 12,
        letterSpacing: "0.12em",
        cursor: disabled ? "not-allowed" : "pointer",
      }}
    >
      + {label}
    </button>
  );
}
