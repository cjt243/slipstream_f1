import { C, FONT } from "../../lib/tokens";
import { Mono } from "../ui";
import { formatGBP } from "../../lib/format";

/** One constructor: name, team-color marker, salary. */
export default function ConstructorCard({ constructor: team }) {
  const color = team.color || C.muted;
  return (
    <div
      className="p-4 rounded-lg flex items-center justify-between"
      style={{ background: C.carbon, border: `1px solid ${C.border}`, borderLeft: `3px solid ${color}` }}
    >
      <div className="flex items-center gap-2 min-w-0">
        <span className="w-3 h-3 rounded-full" style={{ background: color, flexShrink: 0 }} />
        <span
          className="font-bold truncate"
          style={{ fontSize: 15, fontFamily: FONT.display, color: C.white, letterSpacing: "0.04em" }}
        >
          {team.name}
        </span>
      </div>
      <Mono color={C.gold} size="text-sm">{formatGBP(team.salary)}</Mono>
    </div>
  );
}
