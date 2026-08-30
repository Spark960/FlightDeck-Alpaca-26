import { NavLink, Outlet } from "react-router-dom";

import { StatusBadge } from "./StatusBadge";

type LayoutProps = {
  demoMode: boolean;
  paperMode: boolean;
};

const navItems = [
  { to: "/", label: "Cockpit", end: true },
  { to: "/replay", label: "Replay" },
  { to: "/positions", label: "Positions" },
  { to: "/risk", label: "Risk" },
  { to: "/settings", label: "Settings" },
];

export function Layout({ demoMode, paperMode }: LayoutProps) {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand__mark">FDA</span>
          <div>
            <h1>FlightDeck Alpha</h1>
            <p>Autonomous options agent with replayable audit trail</p>
          </div>
        </div>
        <div className="topbar__badges">
          <StatusBadge label={paperMode ? "Paper" : "Live"} tone="ok" />
          <StatusBadge label={demoMode ? "Demo mode" : "Live data"} tone={demoMode ? "warn" : "ok"} />
        </div>
      </header>

      <nav className="nav">
        {navItems.map((item) => (
          <NavLink key={item.to} to={item.to} end={item.end} className="nav__link">
            {item.label}
          </NavLink>
        ))}
      </nav>

      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
