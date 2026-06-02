import { C } from "../../lib/tokens";

/** Carbon panel with optional accent glow. */
export default function Card({ children, accent, style = {} }) {
  return (
    <div
      className="rounded-lg p-5 relative overflow-hidden mb-4"
      style={{
        background: C.carbon,
        border: `1px solid ${accent ? accent + "50" : C.border}`,
        boxShadow: accent ? `0 0 24px ${accent}15` : "none",
        ...style,
      }}
    >
      {accent && (
        <div
          className="absolute top-0 right-0 w-24 h-24 pointer-events-none"
          style={{ background: `radial-gradient(circle at top right, ${accent}20, transparent 70%)` }}
        />
      )}
      {children}
    </div>
  );
}
