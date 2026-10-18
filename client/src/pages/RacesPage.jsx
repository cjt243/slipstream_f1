import { useEffect, useRef } from "react";
import { Label } from "../components/ui";
import { C, FONT } from "../lib/tokens";
import { useRaces } from "../hooks/useRaces";
import RaceCard from "../components/race/RaceCard";

export default function RacesPage() {
  const { races, nextRaceId, loading, error } = useRaces();
  const nextRef = useRef(null);

  // Land on the next race rather than round 1.
  useEffect(() => {
    nextRef.current?.scrollIntoView({ block: "center" });
  }, [nextRaceId, loading]);

  return (
    <>
      <Label>Race Schedule</Label>
      {loading ? (
        <div style={{ fontSize: 13, color: C.ghost, fontFamily: FONT.body }}>Loading…</div>
      ) : error ? (
        <div style={{ fontSize: 13, color: C.danger, fontFamily: FONT.body }}>Couldn't load races: {error}</div>
      ) : races.length === 0 ? (
        <div style={{ fontSize: 13, color: C.ghost, fontFamily: FONT.body }}>No races scheduled yet.</div>
      ) : (
        races.map((race) => (
          <div key={race.id} ref={race.id === nextRaceId ? nextRef : null}>
            <RaceCard race={race} isNext={race.id === nextRaceId} />
          </div>
        ))
      )}
    </>
  );
}
