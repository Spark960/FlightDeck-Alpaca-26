import React, { useEffect, useState } from "react";
import {
  CheckCircle,
  Cpu,
  Play,
  RefreshCw,
  Server,
  Terminal,
  Zap,
} from "lucide-react";
import { api } from "../api/client";
import { JsonViewer }  from "../components/JsonViewer";
import { Modal }       from "../components/Modal";
import { StatusBadge } from "../components/StatusBadge";
import { CliRunResponse, CliStatusResponse, HealthResponse, PublicSettings } from "../types/api";

const PRESETS = [
  { label: "account",   args: "account" },
  { label: "positions", args: "positions" },
  { label: "clock",     args: "clock" },
  { label: "orders",    args: "orders" },
  { label: "version",   args: "version" },
];

export const SettingsPage: React.FC = () => {
  const [settings,      setSettings]      = useState<PublicSettings | null>(null);
  const [health,        setHealth]        = useState<HealthResponse | null>(null);
  const [cliStatus,     setCliStatus]     = useState<CliStatusResponse | null>(null);
  const [cliHistory,    setCliHistory]    = useState<any[]>([]);
  const [loading,       setLoading]       = useState(true);
  const [commandArgs,   setCommandArgs]   = useState("account");
  const [cmdOutput,     setCmdOutput]     = useState<any | null>(null);
  const [isExecCli,     setIsExecCli]     = useState(false);
  const [isRunningProof,setIsRunningProof]= useState(false);
  const [proofResult,   setProofResult]   = useState<CliRunResponse | null>(null);
  const [inspectModal,  setInspectModal]  = useState<{ title: string; data: any } | null>(null);
  const [errorMsg,      setErrorMsg]      = useState<string | null>(null);

  const fetchAll = async () => {
    try {
      setLoading(true); setErrorMsg(null);
      const [sR, hR, cR, histR] = await Promise.allSettled([
        api.getSettings(), api.getHealth(), api.getCliStatus(), api.getCliLatest(15),
      ]);
      if (sR.status    === "fulfilled") setSettings(sR.value);
      if (hR.status    === "fulfilled") setHealth(hR.value);
      if (cR.status    === "fulfilled") setCliStatus(cR.value);
      if (histR.status === "fulfilled") setCliHistory(histR.value);
    } catch (e: any) { setErrorMsg(e.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchAll(); }, []);

  const handleCmd = async (argsOverride?: string) => {
    const raw   = (argsOverride ?? commandArgs).trim();
    const split = raw.split(/\s+/).filter(Boolean);
    if (!split.length) return;
    try {
      setIsExecCli(true); setErrorMsg(null);
      const res = await api.runCliCommand(split);
      setCmdOutput(res.result);
      const hist = await api.getCliLatest(15);
      setCliHistory(hist);
    } catch (e: any) { setErrorMsg(e.message); }
    finally { setIsExecCli(false); }
  };

  const handleProof = async () => {
    try {
      setIsRunningProof(true); setErrorMsg(null);
      const res = await api.runCliProof();
      setProofResult(res);
      const hist = await api.getCliLatest(15);
      setCliHistory(hist);
    } catch (e: any) { setErrorMsg(e.message); }
    finally { setIsRunningProof(false); }
  };

  return (
    <div className="space-y-4">

      {/* Header */}
      <div className="flex items-end justify-between">
        <div>
          <div className="text-[9px] font-bold uppercase tracking-widest text-muted">// MODULE</div>
          <h2 className="font-bold text-[20px] uppercase tracking-tight">CLI &amp; SYSTEM</h2>
          <div className="text-[10px] text-muted uppercase font-bold tracking-widest mt-0.5">
            OFFICIAL ALPACA CLI INTEGRATION · HACKATHON COMPLIANCE PROOF
          </div>
        </div>
        <button onClick={fetchAll} disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-slab border-2 border-rule2 hover:border-rule font-mono font-bold text-[10px] uppercase text-muted hover:text-paper cursor-pointer disabled:opacity-40">
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          REFRESH
        </button>
      </div>

      {errorMsg && (
        <div className="bg-neg text-paper p-3 border-2 border-rule font-mono text-[11px] font-bold flex items-center justify-between">
          <span>ERR: {errorMsg}</span>
          <button onClick={() => setErrorMsg(null)} className="underline cursor-pointer">DISMISS</button>
        </div>
      )}

      {/* Terminal console */}
      <div className="bg-ink border-2 border-pos shadow-hard-g">

        {/* Console title bar */}
        <div className="flex items-center justify-between px-4 py-3 border-b-2 border-pos bg-[#001a00]">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-pos" />
            <span className="font-bold text-[12px] uppercase tracking-widest text-pos">
              ALPACA CLI CONSOLE
            </span>
            {cliStatus?.installed ? (
              <StatusBadge variant="ok" pulse size="sm">INSTALLED</StatusBadge>
            ) : (
              <StatusBadge variant="warn" size="sm">SIMULATED</StatusBadge>
            )}
          </div>
          <button
            onClick={handleProof}
            disabled={isRunningProof}
            className="flex items-center gap-2 px-4 py-2 bg-pos text-ink font-mono font-bold text-[10px] uppercase tracking-widest hover:bg-[#00CC33] disabled:opacity-40 cursor-pointer border-2 border-pos shadow-hard-sm"
          >
            <Zap className="w-3.5 h-3.5" />
            {isRunningProof ? "RUNNING..." : "FULL PROOF SUITE"}
          </button>
        </div>

        {/* Presets row */}
        <div className="flex flex-wrap items-center gap-0 border-b-2 border-slab bg-void px-4 py-2">
          <span className="text-[9px] font-bold uppercase text-rule2 mr-3">PRESETS:</span>
          {PRESETS.map(p => (
            <button
              key={p.args}
              onClick={() => { setCommandArgs(p.args); handleCmd(p.args); }}
              disabled={isExecCli}
              className="px-3 py-1 font-mono text-[10px] font-bold text-pos border-r-2 border-slab hover:bg-[#001a00] cursor-pointer disabled:opacity-40 uppercase"
            >
              $ alpaca {p.label}
            </button>
          ))}
        </div>

        {/* Command input */}
        <div className="flex items-center border-b-2 border-slab bg-ink">
          <span className="px-4 py-3 font-mono font-bold text-pos text-[13px] shrink-0">$</span>
          <span className="font-mono font-bold text-info text-[13px] shrink-0">alpaca</span>
          <input
            type="text"
            value={commandArgs}
            onChange={e => setCommandArgs(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleCmd()}
            placeholder="account"
            className="flex-1 bg-transparent font-mono font-bold text-[13px] text-paper placeholder-[#222222] px-2 py-3 outline-none uppercase"
          />
          <button
            onClick={() => handleCmd()}
            disabled={isExecCli}
            className="flex items-center gap-2 px-5 py-3 bg-pos text-ink font-mono font-bold text-[11px] uppercase tracking-widest hover:bg-[#00CC33] disabled:opacity-40 cursor-pointer border-l-2 border-pos shrink-0"
          >
            <Play className="w-3.5 h-3.5" />
            EXEC
          </button>
        </div>

        {/* Output window */}
        {cmdOutput && (
          <div className="border-b-2 border-slab">
            <div className="flex items-center justify-between px-4 py-2 bg-void border-b border-slab">
              <div className="font-mono text-[10px] font-bold uppercase">
                <span className="text-pos">$ alpaca {Array.isArray(cmdOutput.command) ? cmdOutput.command.join(" ") : cmdOutput.command}</span>
              </div>
              <div className="flex items-center gap-3 font-mono text-[9px] font-bold">
                <span className={cmdOutput.exit_code === 0 ? "text-pos" : "text-neg"}>
                  EXIT:{cmdOutput.exit_code}
                </span>
                <span className="text-rule2">{cmdOutput.duration_ms}ms</span>
              </div>
            </div>
            <pre className="px-4 py-4 font-mono text-[11px] text-pos overflow-x-auto max-h-56 leading-relaxed bg-ink">
              <code>{cmdOutput.stdout || cmdOutput.stderr || "// NO OUTPUT"}</code>
            </pre>
          </div>
        )}

        {/* Proof result */}
        {proofResult && (
          <div className="px-4 py-3 bg-[#001a00] border-b-2 border-pos font-mono text-[11px] font-bold text-pos">
            <div className="flex items-center gap-1.5">
              <CheckCircle className="w-4 h-4" />
              CLI PROOF SUITE COMPLETE
            </div>
            <div className="mt-1 text-[10px] opacity-70 uppercase">
              RUN: {proofResult.run_id} ·
              EXECUTED: {proofResult.summary?.commands_executed} ·
              OK: {proofResult.summary?.commands_succeeded} ·
              FAIL: {proofResult.summary?.commands_failed}
            </div>
          </div>
        )}

        {/* CLI history */}
        {cliHistory.length > 0 && (
          <div className="px-4 py-3">
            <div className="text-[9px] font-bold uppercase text-rule2 mb-2">// RECENT CLI EVENTS (SQLite)</div>
            <table className="w-full font-mono text-[10px]">
              <thead>
                <tr className="border-b-2 border-slab">
                  {["COMMAND", "EXIT", "MS", "TIME", ""].map(h => (
                    <th key={h} className="pb-1.5 text-left text-[9px] font-bold uppercase text-rule2 pr-4">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y-2 divide-[#0A0A0A]">
                {cliHistory.slice(0, 8).map((ev: any, i: number) => (
                  <tr key={i} className="hover:bg-void">
                    <td className="py-1.5 pr-4 text-pos">alpaca {Array.isArray(ev.payload?.command) ? ev.payload.command.join(" ") : (ev.payload?.command || "—")}</td>
                    <td className={`py-1.5 pr-4 ${ev.payload?.exit_code === 0 ? "text-pos" : "text-neg"}`}>
                      {ev.payload?.exit_code ?? 0}
                    </td>
                    <td className="py-1.5 pr-4 text-muted">{ev.payload?.duration_ms ?? "—"}</td>
                    <td className="py-1.5 pr-4 text-rule2">{new Date(ev.created_at).toLocaleTimeString()}</td>
                    <td className="py-1.5 text-right">
                      <button
                        onClick={() => setInspectModal({ title: "CLI EVENT", data: ev })}
                        className="text-rule2 hover:text-y underline cursor-pointer font-bold uppercase"
                      >
                        VIEW
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* System config tables */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

        {/* Backend config */}
        <div className="bg-slab border-2 border-rule2">
          <div className="flex items-center gap-2 px-4 py-3 border-b-2 border-rule2 bg-ink">
            <Server className="w-4 h-4 text-paper" />
            <span className="font-bold text-[11px] uppercase tracking-widest">BACKEND &amp; DEPLOYMENT</span>
          </div>
          <div className="divide-y-2 divide-rule2 font-mono text-[11px]">
            {[
              { k: "APPLICATION",    v: settings?.app || "FlightDeck Alpha",                            c: "#FFFFFF" },
              { k: "PAPER TRADING",  v: settings?.paper_mode ? "LOCKED (ALPACA_PAPER=true)" : "LIVE",   c: settings?.paper_mode ? "#00FF41" : "#FF003C" },
              { k: "DEMO MODE",      v: settings?.demo_mode  ? "ACTIVE (Offline Safe)" : "DISABLED",    c: settings?.demo_mode  ? "#FF8C00" : "#444444" },
              { k: "ALPACA URL",     v: settings?.alpaca_trading_base_url || "—",                       c: "#555555", small: true },
              { k: "HEALTH",         v: health?.status === "ok" ? "HEALTHY (200 OK)" : "INIT",          c: health?.status === "ok" ? "#00FF41" : "#FF8C00" },
            ].map(({ k, v, c, small }) => (
              <div key={k} className="flex items-center justify-between px-4 py-2.5">
                <span className="text-rule2 font-bold uppercase text-[10px]">{k}</span>
                <span className="font-bold truncate max-w-[220px] text-right" style={{ color: c, fontSize: small ? "9px" : "11px" }}>{v}</span>
              </div>
            ))}
          </div>
        </div>

        {/* AI config */}
        <div className="bg-slab border-2 border-violet">
          <div className="flex items-center gap-2 px-4 py-3 border-b-2 border-violet bg-[#0A0010]">
            <Cpu className="w-4 h-4 text-violet" />
            <span className="font-bold text-[11px] uppercase tracking-widest">AI AGENT &amp; SCHEDULER</span>
          </div>
          <div className="divide-y-2 divide-rule2 font-mono text-[11px]">
            {[
              { k: "AGENT MODEL",    v: settings?.agent_model || "gemini-2.5-flash",                                c: "#BF00FF" },
              { k: "LLM PROVIDER",   v: settings?.agent_base_url || "—",                                            c: "#555555", small: true },
              { k: "SCHEDULER",      v: settings?.scheduler_enabled ? "ENABLED (asyncio)" : "MANUAL TRIGGER",       c: settings?.scheduler_enabled ? "#00FF41" : "#555555" },
              { k: "SCAN CADENCE",   v: `EVERY ${settings?.scheduler_interval_minutes || 15} MINUTES`,              c: "#00BFFF" },
              { k: "CLI BINARY",     v: cliStatus?.binary || "alpaca",                                               c: "#555555" },
            ].map(({ k, v, c, small }) => (
              <div key={k} className="flex items-center justify-between px-4 py-2.5">
                <span className="text-rule2 font-bold uppercase text-[10px]">{k}</span>
                <span className="font-bold truncate max-w-[220px] text-right" style={{ color: c, fontSize: small ? "9px" : "11px" }}>{v}</span>
              </div>
            ))}
          </div>
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
