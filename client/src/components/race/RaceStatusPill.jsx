import { C } from "../../lib/tokens";
import { Pill } from "../ui";

const STATUS = {
  upcoming: { label: "UPCOMING", color: C.speed },
  lockdown: { label: "LOCKDOWN", color: C.danger },
  completed: { label: "COMPLETED", color: C.apex },
};

export default function RaceStatusPill({ status }) {
  const s = STATUS[status] || { label: status?.toUpperCase(), color: C.muted };
  return <Pill label={s.label} color={s.color} />;
}
