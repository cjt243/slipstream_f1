import { Card, Label } from "../components/ui";
import { C, FONT } from "../lib/tokens";

// Placeholder — full race schedule UI arrives in issue 2F.
export default function RacesPage() {
  return (
    <>
      <Label>Race Schedule</Label>
      <Card>
        <div style={{ fontSize: 13, color: C.muted, fontFamily: FONT.body }}>
          The season calendar with lockdown timers lands in issue 2F.
        </div>
      </Card>
    </>
  );
}
