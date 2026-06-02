import { Card, Label } from "../components/ui";
import { C, FONT } from "../lib/tokens";

// Placeholder. Issue 2B reads the token from the URL, calls /auth/verify,
// stores the JWT, and redirects to /team.
export default function VerifyPage() {
  return (
    <div
      className="min-h-screen w-full flex items-center justify-center px-4"
      style={{ background: C.void, color: C.white, fontFamily: FONT.body }}
    >
      <div className="w-full max-w-sm">
        <Label>Verifying</Label>
        <Card>
          <div style={{ fontSize: 13, color: C.muted, fontFamily: FONT.body }}>
            Magic-link verification is implemented in issue 2B.
          </div>
        </Card>
      </div>
    </div>
  );
}
