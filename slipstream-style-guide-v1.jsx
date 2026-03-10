import { useState, useMemo } from "react";

// ─────────────────────────────────────────────
// DESIGN TOKENS
// ─────────────────────────────────────────────
const C = {
  void: "#080A0F",
  cockpit: "#0D1117",
  carbon: "#161B22",
  panel: "#1C2333",
  border: "#2A3444",
  // Primary accent — telemetry / information
  speed: "#00E5FF",
  // Overtake / gain — now orange to avoid red=danger confusion
  overtake: "#FF8A2B",
  // Positive / go / completion
  apex: "#00FF88",
  // Top / P1 / gold tier
  gold: "#FFB800",
  // Sprint / improvement
  purple: "#C084FC",
  // Danger / warning / expiry — the ONLY red
  danger: "#FF3D57",
  // Text hierarchy
  white: "#F0F4FF",
  muted: "#A0ADBE",   // bumped from #9BA8BF for contrast
  ghost: "#7B8BA0",   // bumped from #6B7A99 for contrast
};

// Font stacks
const FONT = {
  body: "'Barlow', 'Barlow Condensed', system-ui, sans-serif",
  mono: "'Space Mono', 'Courier New', monospace",
  display: "'Barlow Condensed', 'Barlow', sans-serif",
};

// ─────────────────────────────────────────────
// SCORING DATA
// ─────────────────────────────────────────────
const RACE_SCORING = [
  { pos: "P1", pts: 100 }, { pos: "P2", pts: 97 }, { pos: "P3", pts: 94 },
  { pos: "P5", pts: 88 }, { pos: "P10", pts: 73 }, { pos: "P15", pts: 58 },
  { pos: "P20", pts: 43 }, { pos: "P22", pts: 37 },
];

const QUALI_SCORING = [
  { pos: "P1", pts: 50 }, { pos: "P2", pts: 48 }, { pos: "P3", pts: 46 },
  { pos: "P5", pts: 42 }, { pos: "P10", pts: 32 }, { pos: "P15", pts: 22 },
  { pos: "P22", pts: 8 },
];

const SPRINT_SCORING = [
  { pos: "P1", pts: 22 }, { pos: "P2", pts: 21 }, { pos: "P3", pts: 20 },
  { pos: "P5", pts: 18 }, { pos: "P10", pts: 13 }, { pos: "P15", pts: 8 },
  { pos: "P20", pts: 3 }, { pos: "P22", pts: 1 },
];

const IMPROVEMENT_TABLE = [
  { delta: "+2", pts: 2 }, { delta: "+3", pts: 4 }, { delta: "+4", pts: 6 },
  { delta: "+5", pts: 9 }, { delta: "+6", pts: 12 }, { delta: "+7", pts: 16 },
  { delta: "+8", pts: 20 }, { delta: "+9", pts: 25 }, { delta: "+10", pts: 30 },
];

const BT_TABLE = [
  { margin: "1–3 pos", pts: 2 }, { margin: "4–7 pos", pts: 5 },
  { margin: "8–12 pos", pts: 8 }, { margin: "13+ pos", pts: 12 },
];

const COMPLETION_MILESTONES = [
  { pct: "25%", pts: 3, lap: "Lap 20" },
  { pct: "50%", pts: 3, lap: "Lap 39" },
  { pct: "75%", pts: 3, lap: "Lap 58" },
  { pct: "90%", pts: 3, lap: "Lap 70" },
];

// ─────────────────────────────────────────────
// SHARED COMPONENTS
// ─────────────────────────────────────────────

const Label = ({ children }) => (
  <div className="tracking-widest uppercase mb-4 flex items-center gap-3"
    style={{ color: C.speed, fontSize: 11, fontFamily: FONT.mono, letterSpacing: "0.15em" }}>
    <div className="h-px flex-1" style={{ background: `linear-gradient(to right, ${C.speed}50, transparent)` }} />
    {children}
    <div className="h-px flex-1" style={{ background: `linear-gradient(to left, ${C.speed}50, transparent)` }} />
  </div>
);

const Card = ({ children, accent, style = {} }) => (
  <div className="rounded-lg p-5 relative overflow-hidden mb-4"
    style={{
      background: C.carbon,
      border: `1px solid ${accent ? accent + "50" : C.border}`,
      boxShadow: accent ? `0 0 24px ${accent}15` : "none",
      ...style,
    }}>
    {accent && (
      <div className="absolute top-0 right-0 w-24 h-24 pointer-events-none"
        style={{ background: `radial-gradient(circle at top right, ${accent}20, transparent 70%)` }} />
    )}
    {children}
  </div>
);

const Pill = ({ label, color }) => (
  <span className="font-bold tracking-wider px-2 py-0.5 rounded"
    style={{ fontSize: 11, background: `${color}20`, color, border: `1px solid ${color}40`, fontFamily: FONT.mono }}>
    {label}
  </span>
);

const Mono = ({ children, color = C.white, size = "text-sm" }) => (
  <span className={`${size} font-bold tabular-nums`}
    style={{ fontFamily: FONT.mono, color }}>{children}</span>
);

/** Reusable stat row: left label + right value, optional divider */
const StatRow = ({ label, value, color = C.white, divider = true, step }) => (
  <div className="flex items-center justify-between py-2"
    style={{ borderBottom: divider ? `1px solid ${C.border}` : "none" }}>
    <div className="flex items-center gap-2">
      {step != null && (
        <div className="w-5 h-5 rounded-full flex items-center justify-center"
          style={{ fontSize: 11, background: C.panel, color: C.ghost, fontFamily: FONT.mono, flexShrink: 0 }}>
          {step}
        </div>
      )}
      <span style={{ fontSize: 13, color: C.muted, fontFamily: FONT.body }}>{label}</span>
    </div>
    <Mono color={color} size="text-sm">{value}</Mono>
  </div>
);

/** Toggle button group */
const ToggleGroup = ({ options, value, onChange }) => (
  <div className="mb-4"
    style={{ border: `1px solid ${C.border}`, borderRadius: 6, overflow: "hidden", display: "inline-flex" }}>
    {options.map((t, i) => (
      <button key={t} onClick={() => onChange(t)}
        className="px-4 py-2 tracking-widest uppercase transition-all"
        style={{
          fontSize: 11,
          fontFamily: FONT.mono,
          background: value === t ? `${C.speed}20` : "transparent",
          color: value === t ? C.speed : C.muted,
          border: "none",
          cursor: "pointer",
          borderRight: i < options.length - 1 ? `1px solid ${C.border}` : "none",
        }}>
        {t}
      </button>
    ))}
  </div>
);

// ─────────────────────────────────────────────
// SECTION: Position Scoring
// ─────────────────────────────────────────────

function ScoringSection() {
  const [view, setView] = useState("race");

  const config = {
    race:   { data: RACE_SCORING,   max: 100, accent: C.gold,   formula: "P1=100, −3/pos → P22=37" },
    quali:  { data: QUALI_SCORING,  max: 50,  accent: C.speed,  formula: "P1=50, −2/pos → P22=8" },
    sprint: { data: SPRINT_SCORING, max: 22,  accent: C.purple, formula: "P1=22, −1/pos → P22=1 (Sprint weekends only)" },
  };
  const { data, max, accent, formula } = config[view];

  return (
    <div className="mb-8">
      <Label>Position Scoring</Label>
      <ToggleGroup options={["race", "quali", "sprint"]} value={view} onChange={setView} />

      <Card accent={accent}>
        {data.map(({ pos, pts }) => (
          <div key={pos} className="flex items-center gap-3 mb-2">
            <div className="w-9 font-bold" style={{ fontSize: 13, color: C.muted, fontFamily: FONT.mono }}>{pos}</div>
            <div className="flex-1 h-6 rounded-sm relative overflow-hidden" style={{ background: C.panel }}>
              <div className="h-full rounded-sm transition-all duration-300"
                style={{
                  width: `${(pts / max) * 100}%`,
                  background: pts === max
                    ? `linear-gradient(to right, ${C.gold}, ${C.gold}80)`
                    : pts >= max * 0.7
                      ? `linear-gradient(to right, ${accent}, ${accent}60)`
                      : `linear-gradient(to right, ${C.border}, ${C.ghost})`,
                }} />
              <div className="absolute inset-0 flex items-center px-2">
                <Mono color={pts === max ? C.void : C.white} size="text-xs">{pts} pts</Mono>
              </div>
            </div>
          </div>
        ))}
        <div className="mt-3" style={{ fontSize: 12, color: C.ghost, fontFamily: FONT.body }}>
          {formula}
        </div>
      </Card>
    </div>
  );
}

// ─────────────────────────────────────────────
// SECTION: Overtake Points — now interactive
// ─────────────────────────────────────────────

function OvertakeSection() {
  const [qualiPos, setQualiPos] = useState(10);
  const [finishPos, setFinishPos] = useState(5);

  const gained = Math.max(0, qualiPos - finishPos);
  const pts = gained * 3;

  return (
    <div className="mb-8">
      <Label>Overtake Points (Takes)</Label>
      <Card accent={C.overtake}>
        <div className="mb-4" style={{ fontSize: 13, color: C.muted, fontFamily: FONT.body }}>
          Based on <span style={{ color: C.speed }}>qualifying position</span>, not grid start. +3 pts per position gained. No penalty for losing positions.
        </div>

        {/* Interactive calculator */}
        <div className="p-4 rounded-lg mb-4" style={{ background: C.panel, border: `1px solid ${C.border}` }}>
          <div style={{ fontSize: 11, color: C.ghost, fontFamily: FONT.mono, letterSpacing: "0.1em", marginBottom: 12 }}>
            CALCULATE YOUR TAKES
          </div>
          <div className="flex items-center gap-4 mb-4">
            <div className="flex-1">
              <div style={{ fontSize: 11, color: C.muted, fontFamily: FONT.body, marginBottom: 4 }}>Quali Position</div>
              <div className="flex items-center gap-2">
                <input type="range" min={1} max={22} value={qualiPos}
                  onChange={e => setQualiPos(Number(e.target.value))}
                  style={{ flex: 1, accentColor: C.speed }} />
                <Pill label={`P${qualiPos}`} color={C.muted} />
              </div>
            </div>
            <div style={{ fontSize: 18, color: C.ghost, marginTop: 16 }}>→</div>
            <div className="flex-1">
              <div style={{ fontSize: 11, color: C.muted, fontFamily: FONT.body, marginBottom: 4 }}>Finish Position</div>
              <div className="flex items-center gap-2">
                <input type="range" min={1} max={22} value={finishPos}
                  onChange={e => setFinishPos(Number(e.target.value))}
                  style={{ flex: 1, accentColor: C.apex }} />
                <Pill label={`P${finishPos}`} color={C.apex} />
              </div>
            </div>
          </div>
          <div className="flex items-center justify-between p-3 rounded"
            style={{
              background: gained > 0 ? `${C.overtake}15` : `${C.ghost}15`,
              border: `1px solid ${gained > 0 ? C.overtake + "40" : C.border}`,
            }}>
            <span style={{ fontSize: 13, color: gained > 0 ? C.white : C.ghost, fontFamily: FONT.body }}>
              {gained > 0 ? `+${gained} positions × 3` : finishPos > qualiPos ? "Lost positions — no penalty" : "No change"}
            </span>
            <Mono color={gained > 0 ? C.overtake : C.ghost} size="text-lg">{gained > 0 ? `+${pts}` : "0"} pts</Mono>
          </div>
        </div>

        {/* Quick examples */}
        <div style={{ fontSize: 11, color: C.ghost, fontFamily: FONT.mono, letterSpacing: "0.1em", marginBottom: 8 }}>
          EXAMPLES
        </div>
        {[
          { from: "P10", to: "P5", gained: 5, pts: 15 },
          { from: "P15", to: "P3", gained: 12, pts: 36 },
        ].map(({ from, to, gained: g, pts: p }) => (
          <div key={from + to} className="flex items-center gap-2 mb-2 p-3 rounded"
            style={{ background: C.panel, border: `1px solid ${C.border}` }}>
            <div className="flex items-center gap-2 flex-1">
              <Pill label={from} color={C.muted} />
              <div style={{ fontSize: 13, color: C.ghost }}>→</div>
              <Pill label={to} color={C.apex} />
            </div>
            <span style={{ fontSize: 12, color: C.muted, fontFamily: FONT.body }}>+{g} pos × 3</span>
            <Mono color={C.overtake} size="text-sm">+{p}</Mono>
          </div>
        ))}
        <div className="mt-2 p-3 rounded flex items-center justify-between"
          style={{ background: `${C.ghost}15`, border: `1px dashed ${C.border}` }}>
          <span style={{ fontSize: 12, color: C.ghost, fontFamily: FONT.body }}>Qualified P3 → Finished P8</span>
          <Mono color={C.ghost} size="text-xs">0 pts (no penalty)</Mono>
        </div>
      </Card>
    </div>
  );
}

// ─────────────────────────────────────────────
// SECTION: Improvement Points
// ─────────────────────────────────────────────

function ImprovementSection() {
  return (
    <div className="mb-8">
      <Label>Improvement Points (I.P.)</Label>
      <Card accent={C.purple}>
        <div className="mb-4" style={{ fontSize: 13, color: C.muted, fontFamily: FONT.body }}>
          Awarded when finishing better than <span style={{ color: C.purple }}>8-race rolling average</span>. Minimum 2 positions improvement to earn points.
        </div>
        <div className="grid grid-cols-3 gap-1.5 mb-3">
          {IMPROVEMENT_TABLE.map(({ delta, pts }) => (
            <div key={delta} className="p-2 rounded text-center"
              style={{
                background: pts === 30 ? `${C.purple}20` : C.panel,
                border: `1px solid ${pts === 30 ? C.purple + "50" : C.border}`,
              }}>
              <div className="font-bold" style={{ fontSize: 14, color: pts === 30 ? C.purple : C.white, fontFamily: FONT.mono }}>{pts}</div>
              <div style={{ fontSize: 10, color: C.ghost, fontFamily: FONT.body }}>{delta} pos</div>
            </div>
          ))}
        </div>
        <div className="p-3 rounded flex items-center gap-2"
          style={{ background: `${C.purple}15`, border: `1px solid ${C.purple}30` }}>
          <div style={{ fontSize: 12, color: C.purple, fontFamily: FONT.mono }}>MAX</div>
          <div className="h-px flex-1" style={{ background: C.purple + "40" }} />
          <Mono color={C.purple}>30 pts</Mono>
          <span style={{ fontSize: 12, color: C.muted, fontFamily: FONT.body }}>(10+ pos)</span>
        </div>
      </Card>
    </div>
  );
}

// ─────────────────────────────────────────────
// SECTION: Beat Teammate
// ─────────────────────────────────────────────

function BeatTeammateSection() {
  return (
    <div className="mb-8">
      <Label>Beating Teammate (B.T.)</Label>
      <Card>
        <div className="mb-4" style={{ fontSize: 13, color: C.muted, fontFamily: FONT.body }}>
          Awarded to the driver who finishes ahead of their constructor teammate. Based on margin of positions.
        </div>
        <div className="space-y-2">
          {BT_TABLE.map(({ margin, pts }) => (
            <div key={margin} className="flex items-center gap-3">
              <div className="flex-1 h-7 rounded relative overflow-hidden" style={{ background: C.panel }}>
                <div className="h-full rounded" style={{ width: `${(pts / 12) * 100}%`, background: `${C.gold}60` }} />
                <div className="absolute inset-0 flex items-center px-3">
                  <span style={{ fontSize: 13, color: C.muted, fontFamily: FONT.body }}>{margin}</span>
                </div>
              </div>
              <Mono color={C.gold} size="text-sm">+{pts} pts</Mono>
            </div>
          ))}
        </div>
        <div className="mt-3" style={{ fontSize: 12, color: C.ghost, fontFamily: FONT.body }}>
          Losing teammate earns 0 pts in this category.
        </div>
      </Card>
    </div>
  );
}

// ─────────────────────────────────────────────
// SECTION: Completion Points
// ─────────────────────────────────────────────

function CompletionSection() {
  const [completedTo, setCompletedTo] = useState(4);
  const totalPts = completedTo * 3;

  return (
    <div className="mb-8">
      <Label>Completion Points (Comp)</Label>
      <Card accent={C.apex}>
        <div className="mb-4" style={{ fontSize: 13, color: C.muted, fontFamily: FONT.body }}>
          3 pts earned at each race distance milestone. DNF → earns only milestones completed before retirement. (78-lap example)
        </div>
        <div className="flex gap-2 mb-4">
          {COMPLETION_MILESTONES.map(({ pct, pts, lap }, i) => (
            <button key={pct} onClick={() => setCompletedTo(i + 1)}
              className="flex-1 p-3 rounded transition-all"
              style={{
                background: i < completedTo ? `${C.apex}20` : C.panel,
                border: `1px solid ${i < completedTo ? C.apex + "60" : C.border}`,
                cursor: "pointer",
              }}>
              <div className="font-bold" style={{
                fontSize: 14, fontFamily: FONT.mono,
                color: i < completedTo ? C.apex : C.ghost,
              }}>
                {i < completedTo ? "+3" : "–"}
              </div>
              <div style={{ fontSize: 11, color: i < completedTo ? C.apex : C.ghost, fontFamily: FONT.body }}>{pct}</div>
              <div style={{ fontSize: 10, color: C.ghost, fontFamily: FONT.body }}>{lap}</div>
            </button>
          ))}
        </div>
        <div className="flex items-center justify-between p-3 rounded"
          style={{ background: C.panel, border: `1px solid ${C.border}` }}>
          <span style={{ fontSize: 13, color: C.muted, fontFamily: FONT.body }}>
            {completedTo < 4
              ? `DNF after completing ${COMPLETION_MILESTONES[completedTo - 1].pct} (${COMPLETION_MILESTONES[completedTo - 1].lap})`
              : "Race finished (90%+ completed)"}
          </span>
          <Mono color={C.apex}>+{totalPts} pts</Mono>
        </div>
        <div className="mt-2" style={{ fontSize: 11, color: C.ghost, fontFamily: FONT.body }}>
          Tap milestones to simulate a DNF scenario
        </div>
      </Card>
    </div>
  );
}

// ─────────────────────────────────────────────
// SECTION: Constructor Scoring
// ─────────────────────────────────────────────

function ConstructorSection() {
  return (
    <div className="mb-8">
      <Label>Constructor Scoring (F1)</Label>
      <Card>
        <div className="mb-4" style={{ fontSize: 13, color: C.muted, fontFamily: FONT.body }}>
          Constructors earn qualifying + race points only. No Sprint, Takes, I.P., B.T., or Completion.
        </div>
        <div className="grid grid-cols-2 gap-3 mb-4">
          {[
            { label: "QUALI P1", pts: 30, color: C.speed, note: "−1/pos → P18=13" },
            { label: "RACE P1", pts: 60, color: C.gold, note: "−2/pos → P22=18" },
          ].map(({ label, pts, color, note }) => (
            <div key={label} className="p-4 rounded text-center"
              style={{ background: C.panel, border: `1px solid ${color}40` }}>
              <div className="font-bold" style={{ fontSize: 28, color, fontFamily: FONT.mono }}>{pts}</div>
              <div className="font-bold mt-1" style={{ fontSize: 13, color: C.white, fontFamily: FONT.display }}>{label}</div>
              <div style={{ fontSize: 10, color: C.ghost, fontFamily: FONT.body, marginTop: 4 }}>{note}</div>
            </div>
          ))}
        </div>
        <div className="mb-2" style={{ fontSize: 13, color: C.muted, fontFamily: FONT.body }}>vs. Driver scoring:</div>
        {[
          { cat: "Qualifying P1", driver: "50", constructor: "30", last: false },
          { cat: "Race P1", driver: "100", constructor: "60", last: false },
          { cat: "Sprint, Takes, I.P., B.T., Comp", driver: "✓", constructor: "✗", last: true },
        ].map(({ cat, driver, constructor: cons, last }) => (
          <StatRow key={cat} label={cat}
            value={<><Mono color={C.speed} size="text-xs">{driver}</Mono> <span style={{ color: C.ghost, fontSize: 11 }}>vs</span> <Mono color={cons === "✗" ? C.danger : C.gold} size="text-xs">{cons}</Mono></>}
            divider={!last} />
        ))}
      </Card>
    </div>
  );
}

// ─────────────────────────────────────────────
// SECTION: Max Points
// ─────────────────────────────────────────────

function MaxPointsSection() {
  const categories = [
    { cat: "Race P1", pts: 100, color: C.gold },
    { cat: "Quali P1", pts: 50, color: C.speed },
    { cat: "Sprint P1", pts: 22, color: C.purple },
    { cat: "Takes (18 pos)", pts: 54, color: C.overtake },
    { cat: "I.P. Max", pts: 30, color: C.purple },
    { cat: "B.T. Max", pts: 12, color: C.gold },
    { cat: "Comp (all)", pts: 12, color: C.apex },
  ];
  const total = categories.reduce((s, c) => s + c.pts, 0);
  const maxBar = Math.max(...categories.map(c => c.pts));

  return (
    <div className="mb-8">
      <Label>Max Points Per Event</Label>
      <Card accent={C.gold}>
        <div className="space-y-2 mb-4">
          {categories.map(({ cat, pts, color }) => (
            <div key={cat} className="flex items-center gap-3">
              <div className="w-28" style={{ fontSize: 13, color: C.muted, fontFamily: FONT.body }}>{cat}</div>
              <div className="flex-1 h-6 rounded relative overflow-hidden" style={{ background: C.panel }}>
                <div className="h-full rounded transition-all duration-300"
                  style={{ width: `${(pts / maxBar) * 100}%`, background: `${color}60` }} />
                <div className="absolute inset-0 flex items-center px-2">
                  <Mono color={color} size="text-xs">{pts}</Mono>
                </div>
              </div>
            </div>
          ))}
        </div>
        <div className="flex items-center justify-between p-3 rounded"
          style={{ background: `${C.gold}20`, border: `1px solid ${C.gold}40` }}>
          <span className="font-bold tracking-wider" style={{ fontSize: 11, color: C.gold, fontFamily: FONT.mono }}>
            THEORETICAL MAX (SPRINT WKD)
          </span>
          <Mono color={C.gold} size="text-lg">~{total} pts</Mono>
        </div>
      </Card>
    </div>
  );
}

// ─────────────────────────────────────────────
// SECTION: Contracts
// ─────────────────────────────────────────────

function ContractSection() {
  const [contracts] = useState([
    { driver: "NORRIS", salary: 24.5, races: 3, remaining: 2 },
    { driver: "PIASTRI", salary: 18.2, races: 2, remaining: 2 },
    { driver: "RUSSELL", salary: 21.0, races: 5, remaining: 4 },
  ]);

  return (
    <div className="mb-8">
      <Label>Contract &amp; Salary Mechanics</Label>

      <div className="space-y-3 mb-4">
        {contracts.map(({ driver, salary, races, remaining }) => {
          const completed = races - remaining;
          const earlyReleasePenalty = (salary * 0.03).toFixed(2);
          const isExpiring = remaining <= 1;
          return (
            <div key={driver} className="p-4 rounded-lg"
              style={{ background: C.panel, border: `1px solid ${isExpiring ? C.danger + "50" : C.border}` }}>
              <div className="flex items-center justify-between mb-3">
                <span className="font-bold"
                  style={{ fontSize: 15, fontFamily: FONT.display, color: C.white, letterSpacing: "0.05em" }}>
                  {driver}
                </span>
                <div className="flex items-center gap-2">
                  <Pill label={`£${salary}M`} color={C.speed} />
                  <Pill label={`${remaining}/${races} RACES`} color={isExpiring ? C.danger : C.muted} />
                </div>
              </div>

              {/* Race progress circles */}
              <div className="flex items-center gap-2 mb-2">
                {Array.from({ length: races }, (_, i) => {
                  const isDone = i < completed;
                  const isCurrent = i === completed;
                  const accent = isExpiring ? C.danger : C.speed;
                  return (
                    <div key={i} className="w-6 h-6 rounded-full flex items-center justify-center"
                      style={{
                        background: isDone ? C.ghost : isCurrent ? `${accent}30` : "transparent",
                        border: `1.5px solid ${isDone ? C.ghost : isCurrent ? accent : C.border}`,
                        boxShadow: isCurrent ? `0 0 8px ${accent}60` : "none",
                      }}>
                      {isDone && <div className="w-2 h-2 rounded-full" style={{ background: C.carbon }} />}
                      {isCurrent && <div className="w-2 h-2 rounded-full" style={{ background: accent }} />}
                    </div>
                  );
                })}
                <span style={{ fontSize: 12, color: C.ghost, fontFamily: FONT.body, marginLeft: 4 }}>
                  {completed}/{races} done
                </span>
              </div>

              <div className="flex justify-between">
                <span style={{ fontSize: 11, color: C.ghost, fontFamily: FONT.body }}>Early release: −£{earlyReleasePenalty}M (3%)</span>
                <span style={{ fontSize: 11, color: C.ghost, fontFamily: FONT.body }}>1-race cooldown on release</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Salary Adjustment Mechanic */}
      <Card>
        <div className="font-bold mb-2" style={{ fontSize: 14, color: C.white, fontFamily: FONT.display }}>
          Salary Adjustment (Post-Race)
        </div>
        <div className="mb-4" style={{ fontSize: 13, color: C.muted, fontFamily: FONT.body }}>
          Rank by fantasy pts → lookup default salary → divide delta by 4 → apply ±£2M cap
        </div>
        {[
          { step: "Salary before", val: "£15.8M", color: C.muted },
          { step: "Fantasy rank this race", val: "8th", color: C.white },
          { step: "Default salary for rank 8", val: "£22.8M", color: C.speed },
          { step: "Base variation", val: "+£7.0M", color: C.speed },
          { step: "Adjustment (÷4, floor £100k)", val: "+£1.7M", color: C.apex },
          { step: "New salary", val: "£17.5M", color: C.gold },
        ].map(({ step, val, color }, i) => (
          <StatRow key={step} label={step} value={val} color={color} divider={i < 5} step={i + 1} />
        ))}
        <div className="mt-4 grid grid-cols-2 gap-3">
          <div className="p-3 rounded text-center" style={{ background: C.panel, border: `1px solid ${C.border}` }}>
            <div className="font-bold" style={{ fontSize: 13, color: C.white, fontFamily: FONT.display }}>Driver Cap</div>
            <Mono color={C.speed} size="text-sm">±£2M/event</Mono>
          </div>
          <div className="p-3 rounded text-center" style={{ background: C.panel, border: `1px solid ${C.border}` }}>
            <div className="font-bold" style={{ fontSize: 13, color: C.white, fontFamily: FONT.display }}>Constructor Cap</div>
            <Mono color={C.gold} size="text-sm">±£3M/event</Mono>
          </div>
        </div>
      </Card>
    </div>
  );
}

// ─────────────────────────────────────────────
// SECTION: Team Value — currency fixed to £
// ─────────────────────────────────────────────

function TeamValueSection() {
  const bankBalance = 12_400_000;
  const rosterValue = 87_600_000;
  const teamTotal = bankBalance + rosterValue;
  const floor = 100_000_000;
  const formatM = (n) => `£${(n / 1_000_000).toFixed(1)}M`;

  return (
    <div className="mb-8">
      <Label>Team Value &amp; Budget</Label>
      <Card accent={C.speed}>
        <div className="text-center mb-5">
          <div className="tracking-widest mb-1" style={{ fontSize: 11, color: C.muted, fontFamily: FONT.mono }}>
            TOTAL TEAM VALUE
          </div>
          <div className="font-bold" style={{ fontSize: 32, color: C.speed, fontFamily: FONT.mono }}>
            {formatM(teamTotal)}
          </div>
          <div className="mt-1" style={{ fontSize: 13, color: teamTotal >= floor ? C.apex : C.danger, fontFamily: FONT.body }}>
            {teamTotal >= floor ? `▲ ${formatM(teamTotal - floor)} above floor` : "⚠ Below floor"}
          </div>
        </div>

        {/* Split bar */}
        <div className="h-3 rounded-full overflow-hidden mb-2 flex" style={{ background: C.panel }}>
          <div className="h-full" style={{ width: `${(bankBalance / teamTotal) * 100}%`, background: `${C.apex}80` }} />
          <div className="h-full flex-1" style={{ background: `${C.speed}50` }} />
        </div>
        <div className="flex justify-between mb-5">
          <div>
            <div style={{ fontSize: 12, color: C.apex, fontFamily: FONT.body }}>Bank Balance</div>
            <Mono color={C.apex} size="text-sm">{formatM(bankBalance)}</Mono>
          </div>
          <div className="text-right">
            <div style={{ fontSize: 12, color: C.speed, fontFamily: FONT.body }}>Roster Value</div>
            <Mono color={C.speed} size="text-sm">{formatM(rosterValue)}</Mono>
          </div>
        </div>

        {/* Rules — all £ */}
        <div className="space-y-1">
          {[
            { rule: "Salary ↑ while contracted", effect: "Gain credited to bank", color: C.apex, last: false },
            { rule: "Salary ↓ while contracted", effect: "Loss debited from bank", color: C.danger, last: false },
            { rule: "Team value floor", effect: "Always ≥ £100M", color: C.gold, last: false },
            { rule: "Starting budget", effect: "£100,000,000", color: C.speed, last: true },
          ].map(({ rule, effect, color, last }) => (
            <StatRow key={rule} label={rule} value={effect} color={color} divider={!last} />
          ))}
        </div>
      </Card>
    </div>
  );
}

// ─────────────────────────────────────────────
// SECTION: Value Index
// ─────────────────────────────────────────────

function ValueIndexSection() {
  const drivers = [
    { name: "BEARMAN", rolling: 142, salary: 8.4, adopted: 12 },
    { name: "NORRIS", rolling: 198, salary: 24.5, adopted: 74 },
    { name: "ALBON", rolling: 105, salary: 10.0, adopted: 28 },
  ];

  return (
    <div className="mb-8">
      <Label>Value Index &amp; League Adoption</Label>
      <Card>
        <div className="mb-4" style={{ fontSize: 13, color: C.muted, fontFamily: FONT.body }}>
          Value Index = Rolling Avg Pts ÷ Salary (£M). Higher = more pts per £ spent.
        </div>
        {drivers.map(({ name, rolling, salary, adopted }) => {
          const valueIndex = (rolling / salary).toFixed(1);
          const isUndervalued = parseFloat(valueIndex) > 15;
          return (
            <div key={name} className="mb-3 p-4 rounded-lg"
              style={{ background: C.panel, border: `1px solid ${isUndervalued ? C.apex + "50" : C.border}` }}>
              <div className="flex items-center justify-between mb-3">
                <span className="font-bold"
                  style={{ fontSize: 15, fontFamily: FONT.display, color: C.white, letterSpacing: "0.05em" }}>
                  {name}
                </span>
                <div className="flex items-center gap-2">
                  {isUndervalued && <Pill label="UNDERVALUED" color={C.apex} />}
                  <Mono color={isUndervalued ? C.apex : C.muted} size="text-base">{valueIndex}</Mono>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-3 text-center">
                {[
                  { l: "ROLLING AVG", v: `${rolling} pts`, c: C.speed },
                  { l: "SALARY", v: `£${salary}M`, c: C.white },
                  { l: "ADOPTED", v: `${adopted}%`, c: adopted > 50 ? C.danger : C.muted },
                ].map(({ l, v, c }) => (
                  <div key={l}>
                    <div className="font-bold" style={{ fontSize: 14, color: c, fontFamily: FONT.mono }}>{v}</div>
                    <div style={{ fontSize: 10, color: C.ghost, fontFamily: FONT.body }}>{l}</div>
                  </div>
                ))}
              </div>
              {/* Adoption bar */}
              <div className="mt-3">
                <div className="h-1.5 rounded-full overflow-hidden" style={{ background: C.carbon }}>
                  <div className="h-full rounded-full"
                    style={{ width: `${adopted}%`, background: adopted > 50 ? `${C.danger}80` : `${C.muted}80` }} />
                </div>
                <div className="text-right mt-1" style={{ fontSize: 10, color: C.ghost, fontFamily: FONT.body }}>
                  {adopted > 50 ? "High ownership — less upside" : "Low ownership — potential edge"}
                </div>
              </div>
            </div>
          );
        })}
      </Card>
    </div>
  );
}

// ─────────────────────────────────────────────
// MAIN APP — sticky header + sticky tab bar
// ─────────────────────────────────────────────

const TABS = [
  { id: "scoring", label: "SCORING" },
  { id: "contracts", label: "CONTRACTS" },
  { id: "strategy", label: "STRATEGY" },
];

export default function SlipstreamStyleGuideV3() {
  const [tab, setTab] = useState("scoring");

  return (
    <div className="min-h-screen w-full" style={{ background: C.void, color: C.white, fontFamily: FONT.body }}>

      {/* Scan line overlay */}
      <div className="fixed inset-0 pointer-events-none z-50"
        style={{ backgroundImage: `repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,229,255,0.012) 2px, rgba(0,229,255,0.012) 4px)` }} />

      {/* Sticky Header */}
      <div className="sticky top-0 z-40 px-4 py-3 flex items-center justify-between"
        style={{ background: `${C.cockpit}EE`, borderBottom: `1px solid ${C.border}`, backdropFilter: "blur(12px)" }}>
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 flex items-center justify-center font-bold"
            style={{
              fontSize: 12, fontFamily: FONT.mono,
              background: `linear-gradient(135deg, ${C.speed}, ${C.speed}60)`,
              color: C.void,
              clipPath: "polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)",
            }}>
            S
          </div>
          <span className="tracking-widest" style={{ fontSize: 14, fontFamily: FONT.display, color: C.white, letterSpacing: "0.15em" }}>
            SLIPSTREAM
          </span>
          <span className="px-1.5 py-0.5 ml-1"
            style={{ fontSize: 10, fontFamily: FONT.mono, background: `${C.speed}20`, color: C.speed, border: `1px solid ${C.speed}40` }}>
            v3.0
          </span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full" style={{ background: C.apex, boxShadow: `0 0 8px ${C.apex}` }} />
          <span style={{ fontSize: 12, color: C.muted, fontFamily: FONT.body }}>RACE WEEK</span>
        </div>
      </div>

      {/* Sticky Tab Nav — sits right below header */}
      <div className="sticky z-30 px-4"
        style={{ top: 52, background: `${C.cockpit}EE`, backdropFilter: "blur(12px)" }}>
        <div className="flex gap-0" style={{ borderBottom: `1px solid ${C.border}` }}>
          {TABS.map(({ id, label }) => (
            <button key={id} onClick={() => setTab(id)}
              className="px-4 py-2.5 tracking-widest uppercase transition-all"
              style={{
                fontSize: 12,
                fontFamily: FONT.mono,
                color: tab === id ? C.speed : C.muted,
                background: "none",
                border: "none",
                borderBottom: `2px solid ${tab === id ? C.speed : "transparent"}`,
                cursor: "pointer",
                marginBottom: "-1px",
              }}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="px-4 pb-20 pt-6 max-w-2xl mx-auto">

        {tab === "scoring" && (
          <>
            <ScoringSection />
            <OvertakeSection />
            <ImprovementSection />
            <BeatTeammateSection />
            <CompletionSection />
            <ConstructorSection />
            <MaxPointsSection />
          </>
        )}

        {tab === "contracts" && (
          <>
            <ContractSection />
            <TeamValueSection />
          </>
        )}

        {tab === "strategy" && (
          <>
            <ValueIndexSection />

            {/* DNF Risk */}
            <div className="mb-8">
              <Label>DNF Risk Indicator</Label>
              <Card>
                <div className="mb-4" style={{ fontSize: 13, color: C.muted, fontFamily: FONT.body }}>
                  DNF Ratio = Total DNFs ÷ Total Events. Historical — all seasons in GridRival DB.
                </div>
                {[
                  { name: "MAGNUSSEN", dnf: 0.24, events: 42 },
                  { name: "ALONSO", dnf: 0.11, events: 78 },
                  { name: "VERSTAPPEN", dnf: 0.09, events: 90 },
                ].map(({ name, dnf, events }) => {
                  const risk = dnf > 0.2 ? "HIGH" : dnf > 0.12 ? "MED" : "LOW";
                  const riskColor = dnf > 0.2 ? C.danger : dnf > 0.12 ? C.gold : C.apex;
                  return (
                    <div key={name} className="flex items-center gap-3 mb-2 p-3 rounded"
                      style={{ background: C.panel, border: `1px solid ${C.border}` }}>
                      <div className="flex-1">
                        <div className="font-bold mb-1"
                          style={{ fontSize: 14, fontFamily: FONT.display, color: C.white, letterSpacing: "0.05em" }}>
                          {name}
                        </div>
                        <div className="h-2 rounded-full overflow-hidden" style={{ background: C.carbon }}>
                          <div className="h-full rounded-full" style={{ width: `${Math.min(dnf * 100 * 3, 100)}%`, background: riskColor }} />
                        </div>
                      </div>
                      <Pill label={risk} color={riskColor} />
                      <div className="text-right">
                        <Mono color={riskColor} size="text-sm">{(dnf * 100).toFixed(0)}%</Mono>
                        <div style={{ fontSize: 10, color: C.ghost, fontFamily: FONT.body }}>{events} evts</div>
                      </div>
                    </div>
                  );
                })}
              </Card>
            </div>

            {/* Strategy Tips */}
            <div className="mb-8">
              <Label>Strategic Principles</Label>
              <div className="space-y-3">
                {[
                  { icon: "◈", tip: "Low adoption + high Value Index = biggest edge over your league", color: C.apex },
                  { icon: "◎", tip: "Takes are uncapped — mid-grid qualifiers with race pace are gold", color: C.overtake },
                  { icon: "▲", tip: "Salary gains while contracted go to your bank — hold rising stars", color: C.gold },
                  { icon: "⬡", tip: "1-race cooldown after any release — plan ahead before lockdown", color: C.purple },
                  { icon: "✕", tip: "Early release costs 3% of current salary — time releases carefully", color: C.danger },
                ].map(({ icon, tip, color }) => (
                  <div key={tip} className="flex gap-3 p-4 rounded-lg"
                    style={{ background: C.panel, border: `1px solid ${color}30` }}>
                    <div className="leading-none mt-0.5" style={{ fontSize: 18, color }}>{icon}</div>
                    <div className="leading-relaxed" style={{ fontSize: 13, color: C.muted, fontFamily: FONT.body }}>{tip}</div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
