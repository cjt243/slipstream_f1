import { useMemo, useState } from "react";
import { C, FONT } from "../../lib/tokens";
import { Pill, ToggleGroup } from "../ui";
import { useDrivers } from "../../hooks/useDrivers";
import { useConstructors } from "../../hooks/useConstructors";
import DriverCard from "./DriverCard";
import ConstructorCard from "./ConstructorCard";

const SORTS = ["salary", "name"];

/** Browse the driver/constructor pool: toggle, search, sort, responsive grid. */
export default function RosterBrowser() {
  const [view, setView] = useState("drivers");
  const [sort, setSort] = useState("salary");
  const [query, setQuery] = useState("");

  const { drivers, loading: dl, usingMock: dMock } = useDrivers();
  const { constructors, loading: cl, usingMock: cMock } = useConstructors();

  const isDrivers = view === "drivers";
  const items = isDrivers ? drivers : constructors;
  const loading = isDrivers ? dl : cl;
  const usingMock = isDrivers ? dMock : cMock;

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    const filtered = q
      ? items.filter(
          (it) =>
            it.name.toLowerCase().includes(q) ||
            (it.constructor_name || "").toLowerCase().includes(q)
        )
      : items;
    return [...filtered].sort((a, b) =>
      sort === "name" ? a.name.localeCompare(b.name) : b.salary - a.salary
    );
  }, [items, query, sort]);

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3 mb-3">
        <ToggleGroup options={["drivers", "constructors"]} value={view} onChange={setView} />
        <ToggleGroup options={SORTS} value={sort} onChange={setSort} />
        {usingMock && <Pill label="MOCK DATA" color={C.purple} />}
      </div>

      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={`Search ${view}…`}
        className="w-full mb-4 px-3 py-2 rounded"
        style={{
          background: C.panel,
          border: `1px solid ${C.border}`,
          color: C.white,
          fontFamily: FONT.body,
          fontSize: 14,
          outline: "none",
        }}
      />

      {loading ? (
        <div style={{ fontSize: 13, color: C.ghost, fontFamily: FONT.body }}>Loading…</div>
      ) : visible.length === 0 ? (
        <div style={{ fontSize: 13, color: C.ghost, fontFamily: FONT.body }}>No matches.</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {visible.map((it) =>
            isDrivers ? (
              <DriverCard key={it.id} driver={it} />
            ) : (
              <ConstructorCard key={it.id} constructor={it} />
            )
          )}
        </div>
      )}
    </div>
  );
}
