import { useState } from "react";
import { Card, Label, Mono, StatRow } from "../components/ui";
import { C, FONT } from "../lib/tokens";
import { useAuth } from "../context/AuthContext";
import { useTeam } from "../hooks/useTeam";
import { formatGBP } from "../lib/format";
import LockdownTimer from "../components/race/LockdownTimer";
import ContractCard from "../components/team/ContractCard";
import EmptySlot from "../components/team/EmptySlot";
import SigningSheet from "../components/team/SigningSheet";
import ReleaseSheet from "../components/team/ReleaseSheet";

const SLOTS = { driver: 5, constructor: 1 };

export default function TeamPage() {
  const { user, logout } = useAuth();
  const { team, loading, error, sign, release, setStar } = useTeam();
  const [starError, setStarError] = useState(null);
  const [signing, setSigning] = useState(null); // "driver" | "constructor"
  const [releasing, setReleasing] = useState(null); // contract

  const race = team?.current_race;
  const locked = !race || race.locked;

  return (
    <>
      <div className="flex items-center justify-between mb-4">
        <span style={{ fontSize: 13, color: C.muted, fontFamily: FONT.body }}>{user?.username ?? ""}</span>
        <button
          onClick={logout}
          style={{ fontSize: 11, fontFamily: FONT.mono, color: C.ghost, background: "none", border: "none", cursor: "pointer" }}
        >
          LOG OUT
        </button>
      </div>

      {loading ? (
        <div style={{ fontSize: 13, color: C.ghost }}>Loading…</div>
      ) : error ? (
        <div style={{ fontSize: 13, color: C.danger }}>Couldn't load your team: {error}</div>
      ) : (
        <>
          <Card accent={locked ? C.danger : C.speed}>
            {race ? (
              <div className="mb-3">
                <Mono color={C.speed} size="text-xs">ROUND {race.round}</Mono>
                <div style={{ fontSize: 18, fontFamily: FONT.display, color: C.white, letterSpacing: "0.04em" }}>{race.name}</div>
                {race.locked ? (
                  <div style={{ fontSize: 12, color: C.danger, fontFamily: FONT.mono, letterSpacing: "0.08em" }}>
                    LOCKDOWN — CHANGES REOPEN AFTER THE RACE
                  </div>
                ) : (
                  <LockdownTimer lockdownAt={race.lockdown_at} />
                )}
              </div>
            ) : (
              <div className="mb-3" style={{ fontSize: 13, color: C.muted }}>The season is over.</div>
            )}
            <StatRow label="Cash" value={formatGBP(team.bank_balance)} color={C.apex} />
            <StatRow label="Contracts" value={formatGBP(team.contract_value)} color={C.speed} />
            <StatRow label="Team value" value={formatGBP(team.team_value)} color={C.gold} divider={false} />
          </Card>

          {["driver", "constructor"].map((type) => {
            const signed = team.contracts.filter((c) => c.element_type === type);
            const empty = Math.max(0, SLOTS[type] - signed.length);
            return (
              <section key={type} className="mb-2">
                <Label>
                  {type === "driver" ? "Drivers" : "Constructor"} {signed.length}/{SLOTS[type]}
                </Label>
                {type === "driver" && (
                  <div className="mb-2" style={{ fontSize: 12, color: starError ? C.danger : C.muted, fontFamily: FONT.body }}>
                    {starError ??
                      `Star driver: pick one driver under ${formatGBP(team.star_max_salary)} to score double this race.`}
                  </div>
                )}
                {signed.map((c) => {
                  const eligible = type === "driver" && c.current_salary < team.star_max_salary;
                  const active = team.star_driver_id === c.element_id;
                  const toggle = () =>
                    setStar(active ? null : c.element_id).then(
                      () => setStarError(null),
                      (err) => setStarError(err.message)
                    );
                  return (
                    <ContractCard
                      key={c.id}
                      contract={c}
                      locked={locked}
                      onRelease={setReleasing}
                      star={eligible ? { active, onToggle: toggle } : null}
                    />
                  );
                })}
                {Array.from({ length: empty }, (_, i) => (
                  <EmptySlot
                    key={i}
                    label={type === "driver" ? "Sign driver" : "Sign constructor"}
                    disabled={locked}
                    onClick={() => setSigning(type)}
                  />
                ))}
              </section>
            );
          })}
        </>
      )}

      {signing && team && (
        <SigningSheet elementType={signing} team={team} onSign={sign} onClose={() => setSigning(null)} />
      )}
      {releasing && (
        <ReleaseSheet contract={releasing} onRelease={release} onClose={() => setReleasing(null)} />
      )}
    </>
  );
}
