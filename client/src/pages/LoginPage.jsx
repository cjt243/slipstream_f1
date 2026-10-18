import { useState } from "react";
import { Navigate } from "react-router-dom";
import { C, FONT } from "../lib/tokens";
import { api } from "../lib/api";
import { Card } from "../components/ui";
import AuthShell from "../components/AuthShell";
import { useAuth } from "../context/AuthContext";

const inputStyle = {
  background: C.panel,
  border: `1px solid ${C.border}`,
  color: C.white,
  fontFamily: FONT.body,
  fontSize: 14,
  outline: "none",
};

const fieldLabelStyle = { fontSize: 11, fontFamily: FONT.mono, color: C.ghost, letterSpacing: "0.1em" };

/** Email + username form that requests a magic link (POST /auth/register). */
export default function LoginPage() {
  const { isAuthenticated } = useAuth();
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [status, setStatus] = useState("idle"); // idle | sending | sent | error
  const [error, setError] = useState("");

  if (isAuthenticated) return <Navigate to="/team" replace />;

  const submit = async (e) => {
    e.preventDefault();
    setStatus("sending");
    setError("");
    try {
      await api.post("/auth/register", { email, username }, { auth: false });
      setStatus("sent");
    } catch (err) {
      setError(err.message);
      setStatus("error");
    }
  };

  if (status === "sent") {
    return (
      <AuthShell label="Check Your Email">
        <Card accent={C.apex}>
          <div className="mb-2" style={{ fontSize: 15, color: C.white }}>
            We sent a sign-in link to <span style={{ color: C.speed }}>{email}</span>.
          </div>
          <div className="mb-4" style={{ fontSize: 13, color: C.muted }}>
            It expires in 15 minutes and works once. You can close this tab.
          </div>
          <button
            onClick={() => setStatus("idle")}
            style={{ fontSize: 11, fontFamily: FONT.mono, color: C.ghost, background: "none", border: "none", cursor: "pointer", padding: 0 }}
          >
            USE A DIFFERENT EMAIL
          </button>
        </Card>
      </AuthShell>
    );
  }

  const sending = status === "sending";
  return (
    <AuthShell label="Sign In">
      <Card accent={C.speed}>
        <form onSubmit={submit}>
          <label className="block mb-3">
            <span style={fieldLabelStyle}>EMAIL</span>
            <input
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full mt-1 px-3 py-2 rounded"
              style={inputStyle}
            />
          </label>
          <label className="block mb-4">
            <span style={fieldLabelStyle}>USERNAME</span>
            <input
              type="text"
              required
              maxLength={30}
              autoComplete="nickname"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full mt-1 px-3 py-2 rounded"
              style={inputStyle}
            />
            <span className="block mt-1" style={{ fontSize: 12, color: C.ghost }}>
              Only used when creating a new account.
            </span>
          </label>
          {status === "error" && (
            <div className="mb-3" role="alert" style={{ fontSize: 13, color: C.danger }}>
              {error}
            </div>
          )}
          <button
            type="submit"
            disabled={sending}
            className="w-full py-3 rounded font-bold tracking-widest uppercase"
            style={{
              fontSize: 12,
              fontFamily: FONT.mono,
              background: `${C.speed}20`,
              color: C.speed,
              border: `1px solid ${C.speed}40`,
              cursor: sending ? "wait" : "pointer",
              opacity: sending ? 0.6 : 1,
            }}
          >
            {sending ? "Sending…" : "Send Magic Link"}
          </button>
        </form>
      </Card>
    </AuthShell>
  );
}
