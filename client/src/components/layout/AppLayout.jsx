import { Outlet } from "react-router-dom";
import { C, FONT } from "../../lib/tokens";
import Header from "./Header";
import BottomNav from "./BottomNav";

/** Shared chrome for authenticated pages: header + scrollable content + nav. */
export default function AppLayout() {
  return (
    <div className="min-h-screen w-full" style={{ background: C.void, color: C.white, fontFamily: FONT.body }}>
      <Header />
      <main className="px-4 pt-6 pb-24 max-w-2xl mx-auto">
        <Outlet />
      </main>
      <BottomNav />
    </div>
  );
}
