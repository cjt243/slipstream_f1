import { useParams } from "react-router-dom";
import { Card, Label, Mono } from "../components/ui";
import { C, FONT } from "../lib/tokens";

// Placeholder — race detail (schedule/results/your-team tabs) arrives in 2F/3C.
export default function RaceDetailPage() {
  const { id } = useParams();
  return (
    <>
      <Label>Race Detail</Label>
      <Card>
        <div style={{ fontSize: 13, color: C.muted, fontFamily: FONT.body }}>
          Detail for race <Mono color={C.speed}>#{id}</Mono> — built in issues 2F / 3C.
        </div>
      </Card>
    </>
  );
}
