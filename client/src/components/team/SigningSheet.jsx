import { useMemo, useState } from "react";
import { C, FONT } from "../../lib/tokens";
import { Mono, ToggleGroup } from "../ui";
import { formatDelta, formatGBP } from "../../lib/format";
import { useDrivers } from "../../hooks/useDrivers";
import { useConstructors } from "../../hooks/useConstructors";
import Sheet from "./Sheet";
import Button from "./Button";

/** Pick a driver/constructor and a contract length, then sign. */
export default function SigningSheet({ elementType, team, onSign, onClose }) {
  const isDriver = elementType === "driver";
  const { drivers } = useDrivers();
  const { constructors } = useConstructors();
  const [query, setQuery] = useState("");
  const [picked, setPicked] = useState(null);
  const [length, setLength] = useState(1);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const cash = team.bank_balance;
  const maxLength = Math.min(5, team.current_race?.races_left ?? 5);
  const onTeam = new Set(team.contracts.filter((c) => c.element_type === elementType).map((c) => c.element_id));
  const cooling = new Set(team.cooldown.filter((c) => c.element_type === elementType).map((c) => c.element_id));

  const options = useMemo(() => {
    const items = isDriver ? drivers : constructors;
    const q = query.trim().toLowerCase();
    return items
      .filter((it) => !q || it.name.toLowerCase().includes(q) || (it.constructor_name || "").toLowerCase().includes(q))
      .map((it) => ({
        ...it,
        blocked: onTeam.has(it.id) ? "On your team" : cooling.has(it.id) ? "Cooldown" : it.salary > cash ? "Over budget" : null,
      }))
      .sort((a, b) => b.salary - a.salary);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [drivers, constructors, query, isDriver, cash, team]);

  async function confirm() {
    setBusy(true);
    setError(null);
    try {
      await onSign(elementType, picked.id, length);
      onClose();
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <Sheet title={isDriver ? "Sign a driver" : "Sign a constructor"} onClose={onClose}>
      {picked ? (
        <div>
          <div className="mb-4">
            <div style={{ fontSize: 20, fontFamily: FONT.display, color: C.white }}>{picked.name}</div>
            <div style={{ fontSize: 12, color: C.muted }}>{picked.constructor_name}</div>
          </div>
          <div className="mb-2" style={{ fontSize: 11, fontFamily: FONT.mono, color: C.ghost, letterSpacing: "0.12em" }}>
            CONTRACT LENGTH (RACES)
          </div>
          <ToggleGroup
            options={Array.from({ length: maxLength }, (_, i) => String(i + 1))}
            value={String(length)}
            onChange={(v) => setLength(Number(v))}
          />
          <div style={{ fontSize: 12, color: C.muted, fontFamily: FONT.body }} className="mb-4">
            Races R{team.current_race.round}
            {length > 1 ? `–R${team.current_race.round + length - 1}` : ""}. Salary changes after each race show in
            your team value; you get the post-race salary back when the contract ends.
          </div>
          <div className="flex justify-between py-2" style={{ borderTop: `1px solid ${C.border}` }}>
            <span style={{ fontSize: 13, color: C.muted }}>Salary</span>
            <Mono color={C.speed}>{formatGBP(picked.salary)}</Mono>
          </div>
          <div className="flex justify-between py-2 mb-4" style={{ borderTop: `1px solid ${C.border}` }}>
            <span style={{ fontSize: 13, color: C.muted }}>Cash after signing</span>
            <Mono color={C.apex}>{formatGBP(cash - picked.salary)}</Mono>
          </div>
          {error && <div className="mb-3" style={{ fontSize: 13, color: C.danger }}>{error}</div>}
          <div className="flex gap-3">
            <Button onClick={() => setPicked(null)} tone={C.muted}>Back</Button>
            <Button onClick={confirm} disabled={busy} solid full>
              {busy ? "Signing…" : `Sign for ${length} race${length > 1 ? "s" : ""}`}
            </Button>
          </div>
        </div>
      ) : (
        <>
          <div className="flex justify-between mb-3" style={{ fontSize: 12, fontFamily: FONT.mono, color: C.ghost }}>
            <span>CASH</span>
            <Mono color={C.apex} size="text-xs">{formatGBP(cash)}</Mono>
          </div>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={`Search ${isDriver ? "drivers" : "constructors"}…`}
            className="w-full mb-3 px-3 py-2 rounded"
            style={{ background: C.panel, border: `1px solid ${C.border}`, color: C.white, fontSize: 14, outline: "none" }}
          />
          {options.map((it) => {
            const color = it.constructor_color || it.color || C.muted;
            const delta = formatDelta(it.salary_change);
            return (
              <button
                key={it.id}
                onClick={() => !it.blocked && setPicked(it)}
                disabled={!!it.blocked}
                className="w-full flex items-center justify-between py-2.5 text-left"
                style={{
                  background: "none",
                  border: "none",
                  borderBottom: `1px solid ${C.border}`,
                  opacity: it.blocked ? 0.45 : 1,
                  cursor: it.blocked ? "not-allowed" : "pointer",
                }}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-1 h-7 rounded" style={{ background: color }} />
                  <div className="min-w-0">
                    <div className="truncate" style={{ fontSize: 14, fontFamily: FONT.display, color: C.white }}>{it.name}</div>
                    <div style={{ fontSize: 11, fontFamily: FONT.mono, color: it.blocked ? C.danger : C.ghost }}>
                      {it.blocked || it.constructor_name || " "}
                    </div>
                  </div>
                </div>
                <div className="flex flex-col items-end shrink-0">
                  <Mono color={C.speed} size="text-sm">{formatGBP(it.salary)}</Mono>
                  {delta && <Mono color={it.salary_change > 0 ? C.apex : C.danger} size="text-xs">{delta}</Mono>}
                </div>
              </button>
            );
          })}
        </>
      )}
    </Sheet>
  );
}
