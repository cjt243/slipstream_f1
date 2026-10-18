import { useEffect } from "react";
import { C, FONT } from "../../lib/tokens";

/** Bottom sheet / dialog with a dimmed backdrop. Closes on Escape or backdrop tap. */
export default function Sheet({ title, onClose, children }) {
  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center" role="dialog" aria-modal="true" aria-label={title}>
      <div className="absolute inset-0" style={{ background: `${C.void}CC` }} onClick={onClose} />
      <div
        className="relative w-full sm:max-w-lg max-h-[88vh] flex flex-col rounded-t-xl sm:rounded-xl"
        style={{ background: C.cockpit, border: `1px solid ${C.border}` }}
      >
        <div className="flex items-center justify-between px-5 py-4" style={{ borderBottom: `1px solid ${C.border}` }}>
          <span style={{ fontSize: 16, fontFamily: FONT.display, color: C.white, letterSpacing: "0.06em" }}>{title}</span>
          <button
            onClick={onClose}
            aria-label="Close"
            style={{ background: "none", border: "none", color: C.ghost, fontSize: 20, cursor: "pointer", lineHeight: 1 }}
          >
            ×
          </button>
        </div>
        <div className="overflow-y-auto px-5 py-4">{children}</div>
      </div>
    </div>
  );
}
