import { C, FONT } from "../../lib/tokens";

/** Segmented toggle. `options` is an array of strings; `value` is the active one. */
export default function ToggleGroup({ options, value, onChange }) {
  return (
    <div
      className="mb-4"
      style={{ border: `1px solid ${C.border}`, borderRadius: 6, overflow: "hidden", display: "inline-flex" }}
    >
      {options.map((t, i) => (
        <button
          key={t}
          onClick={() => onChange(t)}
          className="px-4 py-2 tracking-widest uppercase transition-all"
          style={{
            fontSize: 11,
            fontFamily: FONT.mono,
            background: value === t ? `${C.speed}20` : "transparent",
            color: value === t ? C.speed : C.muted,
            border: "none",
            cursor: "pointer",
            borderRight: i < options.length - 1 ? `1px solid ${C.border}` : "none",
          }}
        >
          {t}
        </button>
      ))}
    </div>
  );
}
