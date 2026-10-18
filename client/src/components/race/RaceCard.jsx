import { Link } from "react-router-dom";
import { C, FONT } from "../../lib/tokens";
import { Mono, Pill } from "../ui";
import { formatDay } from "../../lib/format";
import LockdownTimer from "./LockdownTimer";
import RaceStatusPill from "./RaceStatusPill";

/** One calendar row: round, name, circuit, date, status; the next race glows. */
export default function RaceCard({ race, isNext }) {
  const done = race.status === "completed";
  return (
    <Link
      to={`/race/${race.id}`}
      className="block p-4 rounded-lg mb-3"
      style={{
        background: C.carbon,
        border: `1px solid ${isNext ? C.speed + "80" : C.border}`,
        boxShadow: isNext ? `0 0 24px ${C.speed}20` : "none",
        opacity: done ? 0.75 : 1,
        textDecoration: "none",
      }}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 min-w-0">
          <Mono color={isNext ? C.speed : C.ghost} size="text-sm">R{String(race.round).padStart(2, "0")}</Mono>
          <div className="min-w-0">
            <div
              className="font-bold truncate"
              style={{ fontSize: 15, fontFamily: FONT.display, color: C.white, letterSpacing: "0.04em" }}
            >
              {race.name}
            </div>
            <div style={{ fontSize: 12, color: C.muted, fontFamily: FONT.body }}>
              {race.circuit} · {formatDay(race.race_start_at || race.lockdown_at)}
            </div>
          </div>
        </div>
        <div className="flex flex-col items-end gap-1.5 shrink-0">
          <RaceStatusPill status={race.status} />
          {race.has_sprint && <Pill label="SPRINT" color={C.purple} />}
        </div>
      </div>
      {isNext && race.status === "upcoming" && (
        <div className="mt-3 pt-3" style={{ borderTop: `1px solid ${C.border}` }}>
          <LockdownTimer lockdownAt={race.lockdown_at} />
        </div>
      )}
    </Link>
  );
}
