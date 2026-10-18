import { useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import { Card, Label, Mono, Pill, ToggleGroup } from "../components/ui";
import { C, FONT } from "../lib/tokens";
import { useRaces } from "../hooks/useRaces";
import { useWeekend } from "../hooks/useWeekend";
import LockdownTimer from "../components/race/LockdownTimer";
import RaceStatusPill from "../components/race/RaceStatusPill";

const pos = (p) => (p ? `P${p}` : "—");

// The weekend to open on: the latest one that has locked (in progress or just
// finished), else the next one.
function featuredRace(races, nextRaceId) {
  const now = Date.now();
  const started = races.filter((r) => r.lockdown_at && new Date(r.lockdown_at).getTime() <= now);
  return started.length ? started[started.length - 1].id : nextRaceId ?? races[0]?.id;
}

export default function WeekendPage() {
  const { id } = useParams();
  const { races, nextRaceId, loading, error } = useRaces();

  if (loading) return <Muted>Loading…</Muted>;
  if (error) return <div style={{ fontSize: 13, color: C.danger }}>{error}</div>;
  if (!id) {
    const featured = featuredRace(races, nextRaceId);
    return featured ? <Navigate to={`/weekend/${featured}`} replace /> : <Muted>No races this season.</Muted>;
  }
  const index = races.findIndex((r) => String(r.id) === id);
  return <Weekend raceId={id} prev={races[index - 1]} next={races[index + 1]} />;
}

function Weekend({ raceId, prev, next }) {
  const { data, loading, error } = useWeekend(raceId);
  const [tab, setTab] = useState("lineups");

  if (loading) return <Muted>Loading…</Muted>;
  if (error) return <div style={{ fontSize: 13, color: C.danger }}>Couldn't load this weekend: {error}</div>;
  const { race } = data;

  return (
    <>
      <div className="flex items-center justify-between mb-3">
        <StepLink race={prev} dir="prev" />
        <Link
          to={`/race/${race.id}`}
          style={{ fontSize: 11, fontFamily: FONT.mono, color: C.ghost, textDecoration: "none", letterSpacing: "0.1em" }}
        >
          RACE DETAILS
        </Link>
        <StepLink race={next} dir="next" />
      </div>

      <Card accent={data.winners.length ? C.gold : race.status === "upcoming" ? C.speed : undefined}>
        <div className="flex items-center gap-2 mb-1">
          <Mono color={C.speed} size="text-xs">ROUND {race.round}</Mono>
          <RaceStatusPill status={race.status} />
          {race.has_sprint && <Pill label="SPRINT" color={C.purple} />}
          {data.scored && !data.final && <Pill label="LIVE" color={C.apex} />}
        </div>
        <div className="font-bold" style={{ fontSize: 24, fontFamily: FONT.display, color: C.white, letterSpacing: "0.04em" }}>
          {race.name}
        </div>
        {!data.locked && <LockdownTimer lockdownAt={race.lockdown_at} />}
        {data.winners.length > 0 && (
          <div className="mt-2">
            <div style={{ fontSize: 11, fontFamily: FONT.mono, color: C.gold, letterSpacing: "0.15em" }}>
              WEEKEND WINNER{data.winners.length > 1 ? "S" : ""}
            </div>
            <div className="flex items-baseline justify-between gap-3">
              <div style={{ fontSize: 20, fontFamily: FONT.display, color: C.white, letterSpacing: "0.03em" }}>
                {data.winners.map((w) => w.username).join(" & ")}
              </div>
              <Mono color={C.gold} size="text-lg">{data.winners[0].points}</Mono>
            </div>
          </div>
        )}
        {data.locked && !data.final && (
          <div className="mt-2" style={{ fontSize: 12, color: C.muted, fontFamily: FONT.body }}>
            {data.scored
              ? `${race.has_sprint ? "Qualifying and sprint" : "Qualifying"} points so far — race points arrive a few hours after the race.`
              : "Points arrive after qualifying."}
          </div>
        )}
      </Card>

      <ToggleGroup options={["lineups", "qualifying"]} value={tab} onChange={setTab} />
      {tab === "lineups" ? <Lineups data={data} /> : <Qualifying data={data} />}
    </>
  );
}

function Lineups({ data }) {
  return (
    <>
      {data.lineups.length === 0 && data.hidden_lineups === 0 && (
        <Card><Muted>No teams in the league yet.</Muted></Card>
      )}
      {data.lineups.map((lu) => (
        <LineupCard key={lu.user_id} lineup={lu} />
      ))}
      {data.hidden_lineups > 0 && (
        <Card>
          <Muted>
            {data.hidden_lineups} other lineup{data.hidden_lineups === 1 ? "" : "s"} revealed at lockdown.
          </Muted>
        </Card>
      )}
    </>
  );
}

function LineupCard({ lineup }) {
  const [open, setOpen] = useState(lineup.is_current_user);
  const me = lineup.is_current_user;
  return (
    <Card style={{ paddingTop: 12, paddingBottom: 12, background: me ? `${C.speed}10` : undefined }}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between text-left"
        style={{ background: "none", border: "none", cursor: "pointer" }}
        aria-expanded={open}
      >
        <div className="flex items-center gap-3 min-w-0">
          {lineup.rank != null && (
            <Mono color={lineup.rank === 1 ? C.gold : C.ghost} size="text-sm">P{lineup.rank}</Mono>
          )}
          <div className="truncate" style={{ fontSize: 16, fontFamily: FONT.display, color: me ? C.speed : C.white, letterSpacing: "0.03em" }}>
            {lineup.username}
            {me && <span style={{ fontSize: 11, color: C.ghost, fontFamily: FONT.mono }}> · YOU</span>}
          </div>
        </div>
        {lineup.points != null ? (
          <Mono color={lineup.rank === 1 ? C.gold : C.white} size="text-base">{lineup.points}</Mono>
        ) : (
          <Mono color={C.ghost} size="text-xs">{lineup.elements.length}/6</Mono>
        )}
      </button>
      {open && (
        <div className="mt-2">
          {lineup.elements.length === 0 && <Muted>No lineup this weekend.</Muted>}
          {lineup.elements.map((e) => (
            <div
              key={`${e.element_type}-${e.element_id}`}
              className="flex items-center justify-between py-2"
              style={{ borderTop: `1px solid ${C.border}` }}
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-1 h-6 rounded" style={{ background: e.color || C.muted }} />
                <div className="min-w-0">
                  <div className="truncate" style={{ fontSize: 14, fontFamily: FONT.display, color: C.white }}>{e.name}</div>
                  <div style={{ fontSize: 11, fontFamily: FONT.mono, color: C.ghost }}>
                    {e.element_type === "constructor"
                      ? "CONSTRUCTOR"
                      : e.quali_pos || e.race_pos
                        ? `${e.constructor_name ?? ""} · Q ${pos(e.quali_pos)} · R ${pos(e.race_pos)}`
                        : e.constructor_name}
                  </div>
                </div>
              </div>
              <Mono color={e.points ? C.speed : C.ghost} size="text-sm">{e.points ?? "—"}</Mono>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

function Qualifying({ data }) {
  if (data.qualifying.length === 0)
    return (
      <Card>
        <Muted>Qualifying results appear here once they're in.</Muted>
      </Card>
    );
  return (
    <>
      <Label>Grid</Label>
      <Card style={{ paddingTop: 8, paddingBottom: 8 }}>
        {data.qualifying.map((q, i) => (
          <div
            key={q.driver_id}
            className="flex items-center justify-between py-2.5"
            style={{ borderBottom: i < data.qualifying.length - 1 ? `1px solid ${C.border}` : "none" }}
          >
            <div className="flex items-center gap-3 min-w-0">
              <Mono color={q.quali_pos === 1 ? C.gold : C.ghost} size="text-xs">P{String(q.quali_pos).padStart(2, "0")}</Mono>
              <div className="w-1 h-6 rounded" style={{ background: q.constructor_color || C.muted }} />
              <div className="min-w-0">
                <div className="truncate" style={{ fontSize: 14, fontFamily: FONT.display, color: C.white }}>{q.driver_name}</div>
                <div style={{ fontSize: 11, fontFamily: FONT.mono, color: C.ghost }}>
                  {q.constructor_name}
                  {q.picked_by != null && (
                    <span style={{ color: q.picked_by ? C.speed : C.ghost }}>
                      {" "}· {q.picked_by} TEAM{q.picked_by === 1 ? "" : "S"}
                    </span>
                  )}
                </div>
              </div>
            </div>
            {q.quali_pts != null && <Mono color={C.speed} size="text-sm">{q.quali_pts}</Mono>}
          </div>
        ))}
      </Card>
    </>
  );
}

function StepLink({ race, dir }) {
  const style = { fontSize: 12, fontFamily: FONT.mono, textDecoration: "none", minWidth: 56 };
  const align = { textAlign: dir === "prev" ? "left" : "right" };
  if (!race) return <span style={{ ...style, ...align }} />;
  return (
    <Link to={`/weekend/${race.id}`} aria-label={`Round ${race.round} weekend`} style={{ ...style, ...align, color: C.muted }}>
      {dir === "prev" ? `← R${race.round}` : `R${race.round} →`}
    </Link>
  );
}

function Muted({ children }) {
  return <div style={{ fontSize: 13, color: C.muted, fontFamily: FONT.body }}>{children}</div>;
}
