import { useState } from "react";
import { C, FONT } from "../../lib/tokens";
import { Mono } from "../ui";
import { formatGBP } from "../../lib/format";
import Sheet from "./Sheet";
import Button from "./Button";

const PENALTY_RATE = 0.03;

/** Confirm a release: free cancellation before the first race, else 3% penalty. */
export default function ReleaseSheet({ contract, onRelease, onClose }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const free = contract.cancellable;
  const penalty = free ? 0 : Math.round(contract.current_salary * PENALTY_RATE);
  const refund = free ? contract.signed_salary : contract.current_salary - penalty;

  async function confirm() {
    setBusy(true);
    setError(null);
    try {
      await onRelease(contract.id);
      onClose();
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <Sheet title={free ? "Cancel signing" : "Release early"} onClose={onClose}>
      <div className="mb-3" style={{ fontSize: 20, fontFamily: FONT.display, color: C.white }}>{contract.element_name}</div>
      <div className="mb-4" style={{ fontSize: 13, color: C.muted, fontFamily: FONT.body }}>
        {free
          ? "They haven't raced for you yet, so you get the full salary back with no penalty."
          : "Releasing before the contract ends costs 3% of their current salary, and you can't re-sign them for the next race."}
      </div>
      {!free && (
        <div className="flex justify-between py-2" style={{ borderTop: `1px solid ${C.border}` }}>
          <span style={{ fontSize: 13, color: C.muted }}>Penalty</span>
          <Mono color={C.danger}>−{formatGBP(penalty)}</Mono>
        </div>
      )}
      <div className="flex justify-between py-2 mb-4" style={{ borderTop: `1px solid ${C.border}` }}>
        <span style={{ fontSize: 13, color: C.muted }}>Back to cash</span>
        <Mono color={C.apex}>{formatGBP(refund)}</Mono>
      </div>
      {error && <div className="mb-3" style={{ fontSize: 13, color: C.danger }}>{error}</div>}
      <div className="flex gap-3">
        <Button onClick={onClose} tone={C.muted}>Keep</Button>
        <Button onClick={confirm} disabled={busy} tone={C.danger} solid full>
          {busy ? "Releasing…" : free ? "Cancel signing" : "Release"}
        </Button>
      </div>
    </Sheet>
  );
}
