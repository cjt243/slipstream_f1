import { C, FONT } from "../lib/tokens";
import { Label } from "./ui";

/** Centered, header-less page frame for the sign-in flow. */
export default function AuthShell({ label, children }) {
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
        <Label>{label}</Label>
        {children}
      </div>
    </div>
  );
}
