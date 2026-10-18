import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { C, FONT } from "../lib/tokens";
import { api } from "../lib/api";
import { Card } from "../components/ui";
import AuthShell from "../components/AuthShell";
import { useAuth } from "../context/AuthContext";

/** Landing page for the emailed link: exchanges ?token= for a JWT. */
export default function VerifyPage() {
  const [params] = useSearchParams();
  const token = params.get("token");
  const { login } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState(token ? "" : "This sign-in link is missing its token.");
  // Tokens are single-use; StrictMode runs effects twice in dev, so guard.
  const started = useRef(false);

  useEffect(() => {
    if (!token || started.current) return;
    started.current = true;
    api
      .post("/auth/verify", { token }, { auth: false })
      .then((data) => {
        login(data.token, data.user);
        navigate("/team", { replace: true });
      })
      .catch((err) => setError(err.message));
  }, [token, login, navigate]);

  return (
    <AuthShell label={error ? "Sign-In Failed" : "Signing In"}>
      <Card accent={error ? C.danger : C.speed}>
        {error ? (
          <>
            <div className="mb-4" role="alert" style={{ fontSize: 14, color: C.white }}>
              {error}
            </div>
            <Link to="/login" style={{ fontSize: 11, fontFamily: FONT.mono, color: C.speed, textDecoration: "none" }}>
              REQUEST A NEW LINK →
            </Link>
          </>
        ) : (
          <div style={{ fontSize: 14, color: C.muted }}>Verifying your link…</div>
        )}
      </Card>
    </AuthShell>
  );
}
