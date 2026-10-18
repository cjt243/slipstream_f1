import { useState } from "react";
import { Card, Label, Mono } from "../components/ui";
import { C, FONT } from "../lib/tokens";
import { formatGBP } from "../lib/format";
import { useLeaderboard } from "../hooks/useLeaderboard";

export default function LeaderboardPage() {
  const [raceId, setRaceId] = useState("");
  const season = useLeaderboard(null);
  const race = useLeaderboard(raceId || null);
  const races = season.data?.races ?? [];
  const view = raceId ? race : season;

  return (
    <>
      <Label>League Table</Label>
      <select
        value={raceId}
        onChange={(e) => setRaceId(e.target.value)}
        aria-label="Standings for"
        className="w-full mb-4 px-3 py-2 rounded"
        style={{ background: C.panel, border: `1px solid ${C.border}`, color: C.white, fontFamily: FONT.mono, fontSize: 12 }}
      >
        <option value="">SEASON</option>
        {[...races].reverse().map((r) => (
          <option key={r.id} value={r.id}>
            R{r.round} · {r.name}
          </option>
        ))}
      </select>

      {view.loading ? (
        <div style={{ fontSize: 13, color: C.ghost }}>Loading…</div>
      ) : view.error ? (
        <div style={{ fontSize: 13, color: C.danger }}>Couldn't load standings: {view.error}</div>
      ) : (
        <Card style={{ paddingTop: 8, paddingBottom: 8 }}>
          {!raceId && races.length === 0 && (
            <div className="py-2" style={{ fontSize: 12, color: C.muted }}>
              No races scored yet — points arrive after the first race with your teams.
            </div>
          )}
          {view.data.standings.map((s, i) => {
            const me = s.is_current_user;
            const first = s.rank === 1;
            const points = raceId ? s.race_points : s.total_points;
            return (
              <div
                key={s.user_id}
                className="flex items-center justify-between py-3 px-2 -mx-2 rounded"
                style={{
                  borderBottom: i < view.data.standings.length - 1 ? `1px solid ${C.border}` : "none",
                  background: me ? `${C.speed}12` : "transparent",
                }}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <Mono color={first ? C.gold : C.ghost} size="text-sm">P{s.rank}</Mono>
                  <div className="min-w-0">
                    <div
                      className="truncate"
                      style={{ fontSize: 15, fontFamily: FONT.display, color: me ? C.speed : C.white, letterSpacing: "0.03em" }}
                    >
                      {s.username}
                      {me && <span style={{ fontSize: 11, color: C.ghost, fontFamily: FONT.mono }}> · YOU</span>}
                    </div>
                    {!raceId && (
                      <div style={{ fontSize: 11, fontFamily: FONT.mono, color: C.ghost }}>
                        Team value {formatGBP(s.team_value)}
                      </div>
                    )}
                  </div>
                </div>
                <Mono color={first ? C.gold : C.white} size="text-base">{points}</Mono>
              </div>
            );
          })}
        </Card>
      )}
    </>
  );
}
