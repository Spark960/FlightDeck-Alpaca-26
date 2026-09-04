import React, { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  Clock,
  Crosshair,
  History,
  RefreshCw,
  Shield,
  Terminal,
  TrendingUp,
} from "lucide-react";
import { api } from "../api/client";
import { AccountInfo, MarketClock, PublicSettings } from "../types/api";
import { StatusBadge } from "./StatusBadge";

interface LayoutProps {
  children: React.ReactNode;
}

const NAV = [
  { label: "COCKPIT",        path: "/",          icon: Crosshair },
  { label: "POSITIONS",      path: "/positions",  icon: TrendingUp },
  { label: "FLIGHT REC",     path: "/replay",     icon: History },
  { label: "RISK GATE",      path: "/risk",       icon: Shield },
  { label: "CLI PROOF",      path: "/settings",   icon: Terminal },
];

function fmt(v?: number) {
  if (v == null) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency", currency: "USD", minimumFractionDigits: 0, maximumFractionDigits: 0,
  }).format(v);
}

export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const location = useLocation();
  const [account,  setAccount]  = useState<AccountInfo | null>(null);
  const [clock,    setClock]    = useState<MarketClock | null>(null);
  const [settings, setSettings] = useState<PublicSettings | null>(null);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState<string | null>(null);

  const fetchGlobal = async () => {
    try {
      setLoading(true); setError(null);
      const [a, c, s] = await Promise.allSettled([
        api.getAccount(), api.getClock(), api.getSettings(),
      ]);
      if (a.status === "fulfilled") setAccount(a.value);
      if (c.status === "fulfilled") setClock(c.value);
      if (s.status === "fulfilled") setSettings(s.value);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGlobal();
    const t = setInterval(fetchGlobal, 30000);
    return () => clearInterval(t);
  }, []);

  const dayPnL  = account ? account.equity - account.last_equity : 0;
  const dayPnLPc = account?.last_equity ? (dayPnL / account.last_equity) * 100 : 0;
  const isOpen  = clock?.is_open ?? false;

  return (
    <div className="min-h-screen bg-void text-paper flex flex-col font-mono">

      {/* ── MASTHEAD ─────────────────────────────────────────── */}
      <header className="border-b-2 border-rule bg-ink">
        {/* Top strip: logo + live metrics */}
        <div className="flex items-stretch border-b-2 border-rule2">

          {/* Logo block */}
          <Link
            to="/"
            className="flex flex-col justify-center px-4 py-3 border-r-2 border-rule hover:bg-y hover:text-ink group"
            style={{ minWidth: 160 }}
          >
            <div className="text-[10px] font-bold uppercase tracking-widest text-muted group-hover:text-ink">
              ALPACA AI AGENTS
            </div>
            <div className="text-[18px] font-bold leading-tight tracking-tight">
              FLIGHTDECK<span className="text-y group-hover:text-ink">_</span>ALPHA
            </div>
          </Link>

          {/* Market clock */}
          <div className="flex flex-col justify-center px-4 py-2 border-r-2 border-rule2">
            <div className="text-[9px] text-muted uppercase tracking-widest">MARKET</div>
            <div className={`text-[13px] font-bold flex items-center gap-1 ${isOpen ? "text-pos" : "text-neg"}`}>
              {isOpen && <span className="blink">■</span>}
              {isOpen ? "OPEN" : "CLOSED"}
            </div>
          </div>

          {/* Equity */}
          <div className="flex flex-col justify-center px-4 py-2 border-r-2 border-rule2">
            <div className="text-[9px] text-muted uppercase tracking-widest">EQUITY</div>
            <div className="text-[13px] font-bold tabular-nums text-paper">
              {account ? fmt(account.equity) : "—"}
            </div>
          </div>

          {/* Buying power */}
          <div className="flex flex-col justify-center px-4 py-2 border-r-2 border-rule2 hidden sm:flex">
            <div className="text-[9px] text-muted uppercase tracking-widest">BUY PWR</div>
            <div className="text-[13px] font-bold tabular-nums text-muted">
              {account ? fmt(account.buying_power) : "—"}
            </div>
          </div>

          {/* Day P&L */}
          <div className="flex flex-col justify-center px-4 py-2 border-r-2 border-rule2 hidden md:flex">
            <div className="text-[9px] text-muted uppercase tracking-widest">DAY P&amp;L</div>
            <div className={`text-[13px] font-bold tabular-nums ${dayPnL >= 0 ? "text-pos" : "text-neg"}`}>
              {dayPnL >= 0 ? "+" : ""}{fmt(dayPnL)}
            </div>
          </div>

          {/* Status flags */}
          <div className="flex items-center gap-2 px-4 py-2 border-r-2 border-rule2 ml-auto">
            <StatusBadge variant="ok" pulse>PAPER</StatusBadge>
            {settings?.demo_mode && <StatusBadge variant="warn">DEMO</StatusBadge>}
          </div>

          {/* Refresh */}
          <button
            onClick={fetchGlobal}
            disabled={loading}
            className="px-4 py-2 border-l-2 border-rule2 text-muted hover:text-y hover:bg-slab cursor-pointer disabled:opacity-30"
            title="Refresh telemetry"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>

        {/* Nav bar */}
        <nav className="flex items-stretch overflow-x-auto">
          {NAV.map(({ label, path, icon: Icon }) => {
            const isActive = path === "/" ? location.pathname === "/" : location.pathname.startsWith(path);
            return (
              <Link
                key={path}
                to={path}
                className={`flex items-center gap-2 px-5 py-3 text-[11px] font-bold uppercase tracking-widest border-r-2 border-rule2 cursor-pointer whitespace-nowrap ${
                  isActive
                    ? "bg-y text-ink border-r-[#FFE500]"
                    : "text-muted hover:text-paper hover:bg-rule2"
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? "text-ink" : ""}`} />
                {label}
              </Link>
            );
          })}
          {/* Account chip at the end */}
          {account?.account_number && (
            <div className="flex items-center px-4 py-3 text-[10px] text-rule2 ml-auto border-l-2 border-rule2">
              ACC: {account.account_number}
            </div>
          )}
        </nav>
      </header>

      {/* Error */}
      {error && (
        <div className="bg-neg text-paper text-[11px] font-mono font-bold px-4 py-2 border-b-2 border-rule flex items-center justify-between">
          <span>ERR: {error}</span>
          <button onClick={() => setError(null)} className="underline cursor-pointer">DISMISS</button>
        </div>
      )}

      {/* Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-[1440px] mx-auto p-4 md:p-5 space-y-4">
          {children}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t-2 border-rule2 bg-ink px-4 py-2">
        <div className="max-w-[1440px] mx-auto flex items-center justify-between gap-4 text-[9px] font-mono text-rule2">
          <span>FLIGHTDECK ALPHA · ALPACA AI TRADING AGENTS HACKATHON 2026 · DEFINED-RISK DEBIT SPREADS ONLY</span>
          <span className="hidden md:block">ALL 18 RISK GATES ACTIVE · PAPER TRADING LOCKED</span>
        </div>
      </footer>
    </div>
  );
};
