import { useNavigate } from "react-router-dom";
import { C, FONT } from "../lib/tokens";
import { Card, Label } from "../components/ui";
import { useAuth } from "../context/AuthContext";

// Placeholder login. The real magic-link form arrives in issue 2B; for now a
// temporary dev button establishes a session so the app shell is navigable.
export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const devContinue = () => {
    login("dev-token", { id: 0, username: "dev", email: "dev@local", is_admin: true });
    navigate("/team");
  };

  return (
    <div
      className="min-h-screen w-full flex items-center justify-center px-4"
      style={{ background: C.void, color: C.white, fontFamily: FONT.body }}
    >
      <div className="w-full max-w-sm">
        <div className="text-center mb-6">
          <span
            className="tracking-widest"
            style={{ fontSize: 24, fontFamily: FONT.display, color: C.white, letterSpacing: "0.2em" }}
          >
            SLIPSTREAM
          </span>
        </div>
        <Label>Sign In</Label>
        <Card accent={C.speed}>
          <div className="mb-4" style={{ fontSize: 13, color: C.muted, fontFamily: FONT.body }}>
            Magic-link sign in lands in issue 2B.
          </div>
          <button
            onClick={devContinue}
            className="w-full py-3 rounded font-bold tracking-widest uppercase"
            style={{ fontSize: 12, fontFamily: FONT.mono, background: `${C.speed}20`, color: C.speed, border: `1px solid ${C.speed}40`, cursor: "pointer" }}
          >
            Continue (dev)
          </button>
        </Card>
      </div>
    </div>
  );
}
