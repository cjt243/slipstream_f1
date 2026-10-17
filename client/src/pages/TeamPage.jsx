import { Label } from "../components/ui";
import { C, FONT } from "../lib/tokens";
import { useAuth } from "../context/AuthContext";
import RosterBrowser from "../components/roster/RosterBrowser";

// In Tier 1 the Team page surfaces the roster browser (issue 1D). Issue 2D
// turns this into the contract/signing experience with roster slots.
export default function TeamPage() {
  const { user, logout } = useAuth();
  return (
    <>
      <div className="flex items-center justify-between mb-2">
        <span style={{ fontSize: 13, color: C.muted, fontFamily: FONT.body }}>
          {user?.username ? `Signed in as ${user.username}` : "Roster"}
        </span>
        <button
          onClick={logout}
          style={{ fontSize: 11, fontFamily: FONT.mono, color: C.ghost, background: "none", border: "none", cursor: "pointer" }}
        >
          LOG OUT
        </button>
      </div>
      <Label>Roster</Label>
      <RosterBrowser />
    </>
  );
}
