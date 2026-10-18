import { useState } from "react";
import { C, FONT } from "../../lib/tokens";
import { Mono } from "../ui";

// Category colours per the style guide.
const CATEGORIES = [
  { key: "quali_pts", label: "Qualifying", color: C.speed },
  { key: "sprint_pts", label: "Sprint", color: C.purple },
  { key: "race_pts", label: "Race", color: C.gold },
  { key: "overtake_pts", label: "Overtakes", color: C.overtake },
  { key: "improvement_pts", label: "Improvement", color: C.purple },
  { key: "teammate_pts", label: "Beat teammate", color: C.speed },
  { key: "completion_pts", label: "Completion", color: C.apex },
];

const pos = (p) => (p ? `P${p}` : "—");

/** One driver's race score; tap to expand the category breakdown. */
export default function DriverScoreRow({ score, rank }) {
  const [open, setOpen] = useState(false);
  const color = score.constructor_color || C.muted;
  return (
    <div style={{ borderBottom: `1px solid ${C.border}` }}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between py-2.5 text-left"
        style={{ background: "none", border: "none", cursor: "pointer" }}
        aria-expanded={open}
      >
        <div className="flex items-center gap-3 min-w-0">
          <Mono color={rank === 1 ? C.gold : C.ghost} size="text-xs">{String(rank).padStart(2, "0")}</Mono>
          <div className="w-1 h-6 rounded" style={{ background: color }} />
          <div className="min-w-0">
            <div className="truncate" style={{ fontSize: 14, fontFamily: FONT.display, color: C.white, letterSpacing: "0.03em" }}>
              {score.driver_name}
            </div>
            <div style={{ fontSize: 11, fontFamily: FONT.mono, color: C.ghost }}>
              Q {pos(score.quali_pos)} · R {pos(score.race_pos)}
              {score.dnf && <span style={{ color: C.danger }}> · DNF</span>}
            </div>
          </div>
        </div>
        <Mono color={C.speed} size="text-base">{score.total_pts}</Mono>
      </button>
      {open && (
        <div className="pb-3 pl-12 pr-1 grid grid-cols-2 gap-x-4 gap-y-1">
          {CATEGORIES.map((c) => (
            <div key={c.key} className="flex justify-between" style={{ fontSize: 12, fontFamily: FONT.body }}>
              <span style={{ color: C.muted }}>{c.label}</span>
              <Mono color={score[c.key] ? c.color : C.ghost} size="text-xs">{score[c.key]}</Mono>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
