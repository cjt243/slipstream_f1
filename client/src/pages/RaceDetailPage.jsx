import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Card, Label, Mono, Pill, StatRow, ToggleGroup } from "../components/ui";
import { C, FONT } from "../lib/tokens";
import { formatDayTime } from "../lib/format";
import { useRace } from "../hooks/useRaces";
import LockdownTimer from "../components/race/LockdownTimer";
import RaceStatusPill from "../components/race/RaceStatusPill";

const TABS = ["schedule", "results"];

export default function RaceDetailPage() {
  const { id } = useParams();
  const { race, loading, error } = useRace(id);
  const [tab, setTab] = useState("schedule");

  if (loading) return <div style={{ fontSize: 13, color: C.ghost, fontFamily: FONT.body }}>Loading…</div>;
  if (error)
    return (
      <>
        <BackLink />
        <div style={{ fontSize: 13, color: C.danger, fontFamily: FONT.body }}>{error}</div>
      </>
    );

  return (
    <>
      <BackLink />
      <Card accent={race.status === "upcoming" ? C.speed : undefined}>
        <div className="flex items-center gap-2 mb-1">
          <Mono color={C.speed} size="text-xs">ROUND {race.round}</Mono>
          <RaceStatusPill status={race.status} />
          {race.has_sprint && <Pill label="SPRINT" color={C.purple} />}
        </div>
        <div
          className="font-bold"
          style={{ fontSize: 24, fontFamily: FONT.display, color: C.white, letterSpacing: "0.04em" }}
        >
          {race.name}
        </div>
        <div className="mb-3" style={{ fontSize: 13, color: C.muted, fontFamily: FONT.body }}>
          {race.circuit}
        </div>
        {race.status === "upcoming" && <LockdownTimer lockdownAt={race.lockdown_at} />}
      </Card>

      <ToggleGroup options={TABS} value={tab} onChange={setTab} />

      {tab === "schedule" ? (
        <Card>
          <StatRow label="Lockdown" value={formatDayTime(race.lockdown_at)} color={C.gold} />
          <StatRow label="Race start" value={formatDayTime(race.race_start_at)} />
          <StatRow label="Sprint weekend" value={race.has_sprint ? "Yes" : "No"} />
          <StatRow label="Laps" value={race.total_laps ?? "TBC"} divider={false} />
        </Card>
      ) : (
        <Card>
          <div style={{ fontSize: 13, color: C.muted, fontFamily: FONT.body }}>
            {race.results_available ? "Scoring breakdown coming soon." : "Results appear here after the race."}
          </div>
        </Card>
      )}
    </>
  );
}

function BackLink() {
  return (
    <Link
      to="/races"
      className="inline-block mb-3"
      style={{ fontSize: 11, fontFamily: FONT.mono, color: C.ghost, textDecoration: "none", letterSpacing: "0.1em" }}
    >
      ← ALL RACES
    </Link>
  );
}
