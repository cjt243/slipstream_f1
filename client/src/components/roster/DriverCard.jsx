import { C, FONT } from "../../lib/tokens";
import { Mono, Pill } from "../ui";
import { formatGBP } from "../../lib/format";

/** One driver: name, number, constructor badge (team color), salary. */
export default function DriverCard({ driver }) {
  const color = driver.constructor_color || C.muted;
  return (
    <div
      className="p-4 rounded-lg flex items-center justify-between"
      style={{ background: C.carbon, border: `1px solid ${C.border}`, borderLeft: `3px solid ${color}` }}
    >
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <span
            className="font-bold truncate"
            style={{ fontSize: 15, fontFamily: FONT.display, color: C.white, letterSpacing: "0.04em" }}
          >
            {driver.name}
          </span>
          <Mono color={C.ghost} size="text-xs">#{driver.driver_number}</Mono>
        </div>
        <div className="mt-1.5">
          <Pill label={driver.constructor_name} color={color} />
        </div>
      </div>
      <Mono color={C.speed} size="text-sm">{formatGBP(driver.salary)}</Mono>
    </div>
  );
}
