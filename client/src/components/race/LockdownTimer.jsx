import { useEffect, useState } from "react";
import { C, FONT } from "../../lib/tokens";
import { Mono } from "../ui";
import { formatCountdown } from "../../lib/format";

/** Live countdown to lockdown; shows "LOCKED" once it has passed. */
export default function LockdownTimer({ lockdownAt, compact = false }) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);

  const left = formatCountdown(lockdownAt, now);
  if (!lockdownAt) return null;
  if (!left) return <Mono color={C.danger} size={compact ? "text-xs" : "text-sm"}>LOCKED</Mono>;
  return (
    <span className="flex items-baseline gap-2">
      {!compact && (
        <span style={{ fontSize: 11, color: C.ghost, fontFamily: FONT.mono, letterSpacing: "0.1em" }}>
          LOCKS IN
        </span>
      )}
      <Mono color={C.gold} size={compact ? "text-xs" : "text-base"}>{left}</Mono>
    </span>
  );
}
