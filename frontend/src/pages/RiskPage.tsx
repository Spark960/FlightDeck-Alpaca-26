import React, { useEffect, useState } from "react";
import {
  AlertOctagon,
  CheckCircle2,
  DollarSign,
  Play,
  Scale,
  Shield,
  ShieldAlert,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import { api } from "../api/client";
import { JsonViewer }  from "../components/JsonViewer";
import { KpiCard }     from "../components/KpiCard";
import { Modal }       from "../components/Modal";
import { StatusBadge } from "../components/StatusBadge";
import { AccountInfo, PublicSettings, RiskCheckResponse } from "../types/api";

const LIQUID_UNIVERSE = ["SPY","QQQ","IWM","AAPL","NVDA","MSFT","TSLA","META","AMZN","GOOGL","AMD"];

const GATES = [
  { id: "paper_trading_required",              title: "HARD PAPER LOCK",                  desc: "ALPACA_PAPER=true enforced at process level",                    sev: "critical" },
  { id: "max_risk_per_trade_exceeded",         title: "MAX RISK/TRADE (1.5%)",            desc: "Defined loss capped at 1.5% equity per spread",                 sev: "high" },
  { id: "max_daily_loss_exceeded",             title: "DAILY LOSS CIRCUIT (3%)",          desc: "No new entries if intraday equity drawdown > 3%",               sev: "high" },
  { id: "max_drawdown_exceeded",               title: "TOTAL DRAWDOWN HALT (8%)",         desc: "All trading suspended if cumulative drop > 8% from peak",       sev: "critical" },
  { id: "unsupported_or_naked_option_structure",title: "ZERO NAKED OPTIONS",              desc: "Only defined-risk debit spreads permitted",                     sev: "critical" },
  { id: "max_open_option_trades_exceeded",     title: "MAX OPEN POSITIONS (5)",           desc: "Total concurrent options positions capped at 5",                sev: "medium" },
  { id: "max_same_underlying_exposure_exceeded",title: "UNDERLYING CONCENTRATION (2)",   desc: "Max 2 simultaneous positions per underlying symbol",            sev: "medium" },
  { id: "max_total_premium_deployed_exceeded", title: "TOTAL PREMIUM CEILING (20%)",      desc: "Aggregate premium capped at 20% of equity",                     sev: "high" },
  { id: "option_spread_too_wide",              title: "BID/ASK LIQUIDITY FILTER (<20%)",  desc: "Blocks spread > 20% of mid",                                   sev: "medium" },
  { id: "stale_option_quote",                  title: "QUOTE FRESHNESS (<15 MIN)",        desc: "Disallows market data older than 15 minutes",                   sev: "medium" },
  { id: "expiration_too_close",                title: "EXPIRY HORIZON (>7 DTE)",          desc: "Requires 7–30 DTE to manage gamma risk",                       sev: "medium" },
  { id: "inside_end_of_day_entry_cutoff",      title: "EOD ENTRY CUTOFF (10 MIN)",        desc: "No new entries in final 10 minutes of session",                 sev: "low" },
];

const SEV_COLOR: Record<string, string> = {
  critical: "#FF003C",
  high:     "#FF8C00",
  medium:   "#00BFFF",
  low:      "#444444",
};

export const RiskPage: React.FC = () => {
  const [account,      setAccount]      = useState<AccountInfo | null>(null);
  const [loading,      setLoading]      = useState(true);
  const [simSymbol,    setSimSymbol]    = useState("SPY");
  const [simDir,       setSimDir]       = useState<"bullish"|"bearish">("bullish");
  const [simMaxDebit,  setSimMaxDebit]  = useState(1500);
  const [simResult,    setSimResult]    = useState<RiskCheckResponse | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [simError,     setSimError]     = useState<string | null>(null);
  const [inspectModal, setInspectModal] = useState<{ title: string; data: any } | null>(null);

  useEffect(() => {
    api.getAccount()
      .then(setAccount)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleSimulate = async () => {
    try {
      setIsSimulating(true); setSimError(null); setSimResult(null);
      const p = await api.createProposal(simSymbol, simDir, simMaxDebit);
      if (!p.accepted) throw new Error(p.rejection_reason || "SELECTOR: NO VALID STRIKES");
      const r = await api.checkRisk({ proposal: p, proposal_id: p.proposal_id });
      setSimResult(r);
    } catch (e: any) { setSimError(e.message); }
    finally { setIsSimulating(false); }
  };

  const eq             = account?.equity ?? 100000;
  const maxRisk        = eq * 0.015;
  const maxPremium     = eq * 0.20;
  const maxDailyLoss   = eq * 0.03;
  const maxDrawdown    = eq * 0.08;
  const fmt = (v: number) => `$${v.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;

  return (
    <div className="space-y-4">

      {/* Header */}
      <div className="bg-slab border-2 border-neg shadow-hard-r">
        <div className="flex items-center justify-between px-4 py-3 border-b-2 border-neg bg-[#0A0000]">
          <div className="flex items-center gap-3">
            <ShieldAlert className="w-5 h-5 text-neg" />
            <div>
              <div className="font-bold text-[14px] uppercase tracking-widest">DETERMINISTIC RISK GOVERNANCE</div>
              <div className="text-[9px] text-muted font-bold uppercase mt-0.5">
                ALL 18 GATES EVALUATE BEFORE EVERY ORDER · ZERO LLM INFLUENCE ON RISK LOGIC
              </div>
            </div>
          </div>
          <StatusBadge variant="ok" pulse>ALL GATES ARMED</StatusBadge>
        </div>
        <div className="px-4 py-3 font-mono text-[11px] text-muted font-bold uppercase">
          // FLIGHTDECK DECOUPLES LLM GENERATION FROM EXECUTION. EACH PROPOSED TRADE MUST PASS
          // MATHEMATICALLY PURE DETERMINISTIC CHECKS BEFORE ANY ORDER IS ROUTED.
        </div>
      </div>

      {/* KPI strip */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-0 border-2 border-neg">
        <KpiCard label="MAX RISK / TRADE"   value={fmt(maxRisk)}      subtitle="1.5% max defined risk"       icon={Shield}       variant="warn" />
        <KpiCard label="MAX PREMIUM DEPLOY" value={fmt(maxPremium)}   subtitle="20.0% of portfolio equity"   icon={DollarSign}   variant="cyan" />
        <KpiCard label="DAILY LOSS CIRCUIT" value={fmt(maxDailyLoss)} subtitle="3.0% circuit breaker stop"   icon={AlertOctagon} variant="negative" />
        <KpiCard label="TOTAL DRAWDOWN CAP" value={fmt(maxDrawdown)}  subtitle="8.0% hard equity protection"  icon={Scale}        variant="negative" />
      </div>

      {/* Simulator */}
      <div className="bg-slab border-2 border-y shadow-hard-y">
        <div className="flex items-center justify-between px-4 py-3 border-b-2 border-y bg-[#0A0A00]">
          <div className="flex items-center gap-2">
            <Play className="w-4 h-4 text-y" />
            <span className="font-bold text-[12px] uppercase tracking-widest text-y">
              INTERACTIVE RISK GATE SIMULATOR
            </span>
          </div>
          <button
            onClick={handleSimulate}
            disabled={isSimulating}
            className="flex items-center gap-2 px-5 py-2 bg-y text-ink font-mono font-bold text-[11px] uppercase tracking-widest hover:bg-[#CCBB00] disabled:opacity-40 cursor-pointer border-2 border-y shadow-hard-sm"
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            {isSimulating ? "EVALUATING..." : "EVALUATE"}
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-0 divide-x-2 divide-rule2 border-b-2 border-rule2">
          {[
            {
              label: "UNDERLYING SYMBOL",
              input: (
                <select value={simSymbol} onChange={e => setSimSymbol(e.target.value)}
                  className="w-full bg-ink border-2 border-rule2 focus:border-y px-3 py-2 font-mono font-bold text-[13px] text-y outline-none cursor-pointer">
                  {LIQUID_UNIVERSE.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              ),
            },
            {
              label: "DIRECTION",
              input: (
                <select value={simDir} onChange={e => setSimDir(e.target.value as any)}
                  className="w-full bg-ink border-2 border-rule2 focus:border-y px-3 py-2 font-mono font-bold text-[12px] text-paper outline-none cursor-pointer">
                  <option value="bullish">BULL CALL DEBIT SPREAD</option>
                  <option value="bearish">BEAR PUT DEBIT SPREAD</option>
                </select>
              ),
            },
            {
              label: "MAX DEBIT BUDGET ($)",
              input: (
                <input type="number" value={simMaxDebit} min={100} max={10000} step={100}
                  onChange={e => setSimMaxDebit(Number(e.target.value))}
                  className="w-full bg-ink border-2 border-rule2 focus:border-y px-3 py-2 font-mono font-bold text-[14px] text-paper outline-none" />
              ),
            },
          ].map(({ label, input }) => (
            <div key={label} className="px-4 py-3 space-y-2">
              <div className="text-[9px] font-bold uppercase tracking-widest text-muted">{label}</div>
              {input}
            </div>
          ))}
        </div>

        {simError && (
          <div className="m-4 p-3 bg-[#1a0000] border-2 border-neg font-mono text-[11px] font-bold text-neg uppercase">
            ERR: {simError}
          </div>
        )}

        {simResult && (
          <div className={`m-4 p-4 border-2 font-mono text-[11px] font-bold ${
            simResult.approved
              ? "bg-[#001a00] border-pos text-pos"
              : "bg-[#1a0000] border-neg text-neg"
          }`}>
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center gap-1.5 text-[13px]">
                {simResult.approved ? <CheckCircle2 className="w-5 h-5" /> : <XCircle className="w-5 h-5" />}
                {simResult.approved ? "RISK APPROVED — ALL GATES PASSED" : "RISK BLOCKED"}
              </div>
              <button
                onClick={() => setInspectModal({ title: "RISK RESULT", data: simResult })}
                className="text-[10px] underline cursor-pointer opacity-60 hover:opacity-100"
              >
                INSPECT JSON
              </button>
            </div>
            {simResult.approved && (
              <div className="mt-2 text-[10px] opacity-80">
                MAX_LOSS: ${simResult.computed_risk?.max_loss} ({simResult.computed_risk?.risk_pct_of_equity}% EQ)
              </div>
            )}
            {!simResult.approved && simResult.blocking_reasons.length > 0 && (
              <ul className="mt-2 space-y-0.5 text-warn text-[10px]">
                {simResult.blocking_reasons.map((r, i) => (
                  <li key={i} className="before:content-['→'] before:mr-1.5">{r}</li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>

      {/* Gate matrix */}
      <div className="bg-slab border-2 border-rule2">
        <div className="px-4 py-3 border-b-2 border-rule2 bg-ink flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-pos" />
          <span className="font-bold text-[12px] uppercase tracking-widest">12-GATE POLICY MATRIX</span>
          <span className="text-[9px] font-bold text-rule2 ml-2">// SOURCE: backend/app/trading/risk.py</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full font-mono text-[11px]">
            <thead>
              <tr className="bg-ink border-b-2 border-rule2">
                {["#", "GATE POLICY", "DESCRIPTION", "CODE ID", "SEV", "ARMED"].map(h => (
                  <th key={h} className="px-3 py-2 text-[9px] font-bold uppercase tracking-widest text-rule2 text-left">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y-2 divide-[#0D0D0D]">
              {GATES.map((g, i) => (
                <tr key={g.id} className="hover:bg-rule2">
                  <td className="px-3 py-3 text-rule2 font-bold">{String(i+1).padStart(2,"0")}</td>
                  <td className="px-3 py-3 font-bold text-paper">{g.title}</td>
                  <td className="px-3 py-3 text-muted max-w-xs">{g.desc}</td>
                  <td className="px-3 py-3 text-[10px] text-info">{g.id}</td>
                  <td className="px-3 py-3">
                    <span
                      className="font-bold text-[9px] uppercase border-2 px-1.5 py-0.5"
                      style={{ color: SEV_COLOR[g.sev], borderColor: SEV_COLOR[g.sev] }}
                    >
                      {g.sev.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-3 py-3 text-center">
                      <CheckCircle2 className="w-4 h-4 mx-auto text-pos" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {inspectModal && (
        <Modal isOpen onClose={() => setInspectModal(null)} title={inspectModal.title}>
          <JsonViewer data={inspectModal.data} title={inspectModal.title} />
        </Modal>
      )}
    </div>
  );
};
