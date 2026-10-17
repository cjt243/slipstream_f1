import { Card, Label } from "../components/ui";
import { C, FONT } from "../lib/tokens";

// Placeholder — standings table arrives in issue 3E.
export default function LeaderboardPage() {
  return (
    <>
      <Label>Leaderboard</Label>
      <Card>
        <div style={{ fontSize: 13, color: C.muted, fontFamily: FONT.body }}>
          Season &amp; per-race standings land in issue 3E.
        </div>
      </Card>
    </>
  );
}
