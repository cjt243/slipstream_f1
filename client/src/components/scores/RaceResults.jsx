import { useState } from "react";
import { C, FONT } from "../../lib/tokens";
import { Card, Mono, ToggleGroup } from "../ui";
import { useScores } from "../../hooks/useScores";
import DriverScoreRow from "./DriverScoreRow";

/** Results tab: fantasy points per driver (expandable) and per constructor. */
export default function RaceResults({ race }) {
  const [view, setView] = useState("drivers");
  const { drivers, constructors, loading, error } = useScores(race.id, race.results_available);

  if (!race.results_available)
    return (
      <Card>
        <div style={{ fontSize: 13, color: C.muted, fontFamily: FONT.body }}>Results appear here after the race.</div>
      </Card>
    );
  if (loading) return <div style={{ fontSize: 13, color: C.ghost, fontFamily: FONT.body }}>Loading…</div>;
  if (error) return <div style={{ fontSize: 13, color: C.danger, fontFamily: FONT.body }}>{error}</div>;

  return (
    <>
      <ToggleGroup options={["drivers", "constructors"]} value={view} onChange={setView} />
      <Card style={{ paddingTop: 8, paddingBottom: 8 }}>
        {view === "drivers"
          ? drivers.map((s, i) => <DriverScoreRow key={s.driver_id} score={s} rank={i + 1} />)
          : constructors.map((s, i) => (
              <div
                key={s.constructor_id}
                className="flex items-center justify-between py-2.5"
                style={{ borderBottom: i < constructors.length - 1 ? `1px solid ${C.border}` : "none" }}
              >
                <div className="flex items-center gap-3">
                  <Mono color={i === 0 ? C.gold : C.ghost} size="text-xs">{String(i + 1).padStart(2, "0")}</Mono>
                  <div className="w-1 h-6 rounded" style={{ background: s.constructor_color || C.muted }} />
                  <div>
                    <div style={{ fontSize: 14, fontFamily: FONT.display, color: C.white }}>{s.constructor_name}</div>
                    <div style={{ fontSize: 11, fontFamily: FONT.mono, color: C.ghost }}>
                      Q {s.quali_pts} · R {s.race_pts}
                    </div>
                  </div>
                </div>
                <Mono color={C.speed} size="text-base">{s.total_pts}</Mono>
              </div>
            ))}
      </Card>
    </>
  );
}
