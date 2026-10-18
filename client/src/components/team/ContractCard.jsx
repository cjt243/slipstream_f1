import { C, FONT } from "../../lib/tokens";
import { Mono } from "../ui";
import { formatDelta, formatGBP } from "../../lib/format";

/** A signed driver/constructor: contract span, value movement, release action. */
export default function ContractCard({ contract, locked, onRelease }) {
  const color = contract.element_color || C.muted;
  const gain = contract.current_salary - contract.signed_salary;
  const span =
    contract.contract_length === 1
      ? `R${contract.race_start}`
      : `R${contract.race_start}–R${contract.last_round}`;
  return (
    <div
      className="p-4 rounded-lg mb-3"
      style={{ background: C.carbon, border: `1px solid ${C.border}`, borderLeft: `3px solid ${color}` }}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="font-bold truncate" style={{ fontSize: 15, fontFamily: FONT.display, color: C.white, letterSpacing: "0.04em" }}>
            {contract.element_name}
          </div>
          <div style={{ fontSize: 12, color: C.muted, fontFamily: FONT.body }}>
            {contract.constructor_name ? `${contract.constructor_name} · ` : ""}
            {span} · {contract.races_remaining} race{contract.races_remaining === 1 ? "" : "s"} left
          </div>
        </div>
        <div className="flex flex-col items-end shrink-0">
          <Mono color={C.speed} size="text-sm">{formatGBP(contract.current_salary)}</Mono>
          {gain !== 0 && (
            <Mono color={gain > 0 ? C.apex : C.danger} size="text-xs">{formatDelta(gain)}</Mono>
          )}
        </div>
      </div>
      <div className="mt-3 flex justify-end">
        <button
          onClick={() => onRelease(contract)}
          disabled={locked}
          style={{
            fontSize: 11,
            fontFamily: FONT.mono,
            letterSpacing: "0.1em",
            color: locked ? C.ghost : C.danger,
            background: "none",
            border: "none",
            cursor: locked ? "not-allowed" : "pointer",
          }}
        >
          {contract.cancellable ? "CANCEL" : "RELEASE"}
        </button>
      </div>
    </div>
  );
}
