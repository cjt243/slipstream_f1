import { NavLink } from "react-router-dom";
import { C, FONT } from "../../lib/tokens";

const TABS = [
  { to: "/team", label: "TEAM" },
  { to: "/races", label: "RACES" },
  { to: "/leaderboard", label: "TABLE" },
];

/** Mobile-first bottom tab bar. */
export default function BottomNav() {
  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-40 flex"
      style={{
        background: `${C.cockpit}F2`,
        borderTop: `1px solid ${C.border}`,
        backdropFilter: "blur(12px)",
      }}
    >
      {TABS.map(({ to, label }) => (
        <NavLink
          key={to}
          to={to}
          className="flex-1 py-3 text-center tracking-widest uppercase transition-all"
          style={({ isActive }) => ({
            fontSize: 12,
            fontFamily: FONT.mono,
            color: isActive ? C.speed : C.muted,
            borderTop: `2px solid ${isActive ? C.speed : "transparent"}`,
            marginTop: "-1px",
          })}
        >
          {label}
        </NavLink>
      ))}
    </nav>
  );
}
