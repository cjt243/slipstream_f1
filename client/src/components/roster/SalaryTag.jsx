import { C } from "../../lib/tokens";
import { Mono } from "../ui";
import { formatDelta, formatGBP } from "../../lib/format";

/** Salary with its last post-race movement underneath. */
export default function SalaryTag({ salary, change, color = C.speed }) {
  const delta = formatDelta(change);
  return (
    <div className="flex flex-col items-end shrink-0">
      <Mono color={color} size="text-sm">{formatGBP(salary)}</Mono>
      {delta && (
        <Mono color={change > 0 ? C.apex : C.danger} size="text-xs">{delta}</Mono>
      )}
    </div>
  );
}
