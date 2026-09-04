import React, { useEffect, useState } from "react";
import {
  Brain,
  CheckCircle,
  Compass,
  FileCode,
  History,
  Layers,
  RefreshCw,
  Search,
  ShieldCheck,
  Terminal,
  XCircle,
} from "lucide-react";
import { api } from "../api/client";
import { EmptyState }  from "../components/EmptyState";
import { JsonViewer }  from "../components/JsonViewer";
import { Modal }       from "../components/Modal";
import { StatusBadge } from "../components/StatusBadge";
import { AuditRunDetail, AuditRunItem } from "../types/api";

const TYPE_CFG: Record<string, { label: string; color: string }> = {
  market_scan:      { label: "SCAN",      color: "#00BFFF" },
  trade_proposal:   { label: "PROPOSE",   color: "#BF00FF" },
  agent_review:     { label: "AI REVIEW", color: "#BF00FF" },
  risk_check:       { label: "RISK",      color: "#FF8C00" },
  trade_execution:  { label: "EXECUTE",   color: "#00FF41" },
  position_monitor: { label: "MONITOR",   color: "#00BFFF" },
  alpaca_cli_proof: { label: "CLI PROOF", color: "#FFE500" },
};

const FILTERS = [
  { id: "all",             label: "ALL" },
  { id: "trade_execution", label: "EXECUTE" },
  { id: "trade_proposal",  label: "PROPOSE" },
  { id: "risk_check",      label: "RISK" },
  { id: "market_scan",     label: "SCAN" },
  { id: "position_monitor",label: "MONITOR" },
];

/** Returns a formatted date string or "—" if the input is invalid/missing. */
const safeDate = (ts: string | undefined | null, format: "time" | "full" = "full"): string => {
  if (!ts) return "—";
  const d = new Date(ts);
  if (isNaN(d.getTime())) return "—";
  return format === "time" ? d.toLocaleTimeString() : d.toLocaleString();
};

export const ReplayPage: React.FC = () => {
  const [runs,          setRuns]          = useState<AuditRunItem[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [runDetail,     setRunDetail]     = useState<AuditRunDetail | null>(null);
  const [loadingRuns,   setLoadingRuns]   = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [filterType,    setFilterType]    = useState("all");
  const [searchTerm,    setSearchTerm]    = useState("");
  const [inspectorData, setInspectorData] = useState<{ title: string; data: any } | null>(null);
  const [errorMsg,      setErrorMsg]      = useState<string | null>(null);

  const fetchRuns = async () => {
    try {
      setLoadingRuns(true); setErrorMsg(null);
      const data = await api.listRuns(100);
      setRuns(data);
      if (data.length > 0 && !selectedRunId) setSelectedRunId(data[0].run_id);
    } catch (e: any) { setErrorMsg(e.message); }
    finally { setLoadingRuns(false); }
  };

  const fetchDetail = async (id: string) => {
    try {
      setLoadingDetail(true); setErrorMsg(null);
      setRunDetail(await api.getRunDetail(id));
    } catch (e: any) { setErrorMsg(e.message); }
    finally { setLoadingDetail(false); }
  };

  useEffect(() => { fetchRuns(); }, []);
  useEffect(() => { if (selectedRunId) fetchDetail(selectedRunId); }, [selectedRunId]);

  const filtered = runs.filter(r =>
    (filterType === "all" || r.run_type === filterType) &&
    (!searchTerm || (r.run_id ?? "").toLowerCase().includes(searchTerm.toLowerCase()) || (r.run_type ?? "").toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="space-y-4">

      <div className="flex items-end justify-between">
        <div>
          <div className="text-[9px] font-bold uppercase tracking-widest text-muted">// MODULE</div>
          <h2 className="font-bold text-[20px] uppercase tracking-tight">FLIGHT RECORDER</h2>
          <div className="text-[10px] text-muted uppercase font-bold tracking-widest mt-0.5">
            100% DETERMINISTIC AUDIT · SQLITE PERSISTENT · EVERY DECISION LOGGED
          </div>
        </div>
        <button
          onClick={fetchRuns}
          disabled={loadingRuns}
          className="flex items-center gap-2 px-4 py-2 bg-slab border-2 border-rule2 hover:border-rule font-mono font-bold text-[10px] uppercase text-muted hover:text-paper cursor-pointer disabled:opacity-40"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loadingRuns ? "animate-spin" : ""}`} />
          REFRESH
        </button>
      </div>

      {errorMsg && (
        <div className="bg-neg text-paper p-3 border-2 border-rule font-mono text-[11px] font-bold">
          ERR: {errorMsg}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">

        {/* Left — Run list */}
        <div className="lg:col-span-4 space-y-3">

          {/* Search + filters */}
          <div className="bg-slab border-2 border-rule2 p-3 space-y-2">
            <div className="relative">
              <Search className="w-3 h-3 absolute left-2.5 top-2.5 text-rule2" />
              <input
                type="text"
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                placeholder="SEARCH RUN ID..."
                className="w-full bg-ink border-2 border-rule2 focus:border-y pl-7 pr-3 py-1.5 text-[10px] font-mono font-bold text-paper placeholder-[#333333] uppercase outline-none"
              />
            </div>
            <div className="flex flex-wrap gap-1">
              {FILTERS.map(f => (
                <button
                  key={f.id}
                  onClick={() => setFilterType(f.id)}
                  className={`px-2 py-1 font-mono text-[9px] font-bold uppercase border-2 cursor-pointer ${
                    filterType === f.id
                      ? "bg-y text-ink border-y"
                      : "bg-ink text-muted border-rule2 hover:border-[#555555] hover:text-paper"
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {/* Runs */}
          <div className="bg-slab border-2 border-rule2 max-h-[620px] overflow-y-auto">
            {loadingRuns && runs.length === 0 ? (
              <div className="p-6 font-mono text-[10px] font-bold text-rule2 uppercase">
                <span className="blink">▶</span> LOADING AUDIT TRAIL...
              </div>
            ) : filtered.length === 0 ? (
              <div className="p-6 font-mono text-[10px] font-bold text-rule2 uppercase">
                // NO RUNS MATCH FILTER
              </div>
            ) : (
              <div className="divide-y-2 divide-rule2">
                {filtered.map(r => {
                  const cfg = TYPE_CFG[r.run_type];
                  const sel = selectedRunId === r.run_id;
                  return (
                    <div
                      key={r.run_id}
                      onClick={() => setSelectedRunId(r.run_id)}
                      className={`p-3 cursor-pointer border-l-4 ${sel ? "bg-rule2" : "hover:bg-[#141414]"}`}
                      style={{ borderLeftColor: sel ? (cfg?.color ?? "#FFFFFF") : "#222222" }}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span
                          className="font-mono font-bold text-[9px] uppercase border-2 px-1.5 py-0.5"
                          style={{ color: cfg?.color ?? "#FFFFFF", borderColor: cfg?.color ?? "#333333" }}
                        >
                          {cfg?.label ?? (r.run_type ?? "unknown").toUpperCase()}
                        </span>
                        <span className="font-mono text-[9px] text-rule2 font-bold">
                          {safeDate(r.started_at, "time")}
                        </span>
                      </div>
                      <div className="mt-1 font-mono text-[10px] font-bold text-paper truncate" title={r.run_id}>
                        {r.run_id}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right — Detail */}
        <div className="lg:col-span-8">
          {!runDetail ? (
            <div className="bg-slab border-2 border-rule2">
              <EmptyState icon={History} title="Select an audit run" description="Pick any run to replay its full decision pipeline." />
            </div>
          ) : loadingDetail ? (
            <div className="bg-slab border-2 border-rule2 p-8 font-mono text-[10px] font-bold text-rule2 uppercase">
              <span className="blink">▶</span> LOADING RUN DETAIL...
            </div>
          ) : (
            <div className="space-y-3">

              {/* Run header */}
              <div className="bg-slab border-2 border-rule px-4 py-3 flex items-center justify-between gap-3 shadow-hard-muted">
                <div>
                  <div className="flex items-center gap-2">
                    <span
                      className="font-mono font-bold text-[9px] uppercase border-2 px-1.5 py-0.5"
                      style={{
                        color:       TYPE_CFG[runDetail.run_type]?.color ?? "#FFFFFF",
                        borderColor: TYPE_CFG[runDetail.run_type]?.color ?? "#333333",
                      }}
                    >
                      {TYPE_CFG[runDetail.run_type]?.label ?? (runDetail.run_type ?? "unknown").toUpperCase()}
                    </span>
                    <span className="font-mono font-bold text-[12px] text-paper">{runDetail.run_id}</span>
                  </div>
                  <div className="mt-1 font-mono text-[9px] text-muted font-bold uppercase">
                    {safeDate(runDetail.started_at, "full")}
                  </div>
                </div>
                <button
                  onClick={() => setInspectorData({ title: runDetail.run_id, data: runDetail })}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-ink border-2 border-rule2 hover:border-y font-mono font-bold text-[9px] uppercase text-muted hover:text-y cursor-pointer"
                >
                  <FileCode className="w-3 h-3" />
                  FULL JSON
                </button>
              </div>

              {/* Steps 01–05 */}
              {[
                {
                  num: "01", label: "MARKET UNIVERSE SNAPSHOT", show: !!runDetail.market_snapshot,
                  icon: Compass, color: "#00BFFF",
                  body: () => <p className="text-[11px] text-muted font-mono">Universe snapshots and 30-day historical bars at execution tick.</p>,
                  jsonKey: "market_snapshot",
                },
                {
                  num: "02", label: "OPTIONS STRATEGY PROPOSAL", show: !!runDetail.trade_proposal,
                  icon: Layers, color: "#BF00FF",
                  body: () => (
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-0 divide-x-2 divide-rule2 font-mono text-[10px]">
                      {[
                        { l: "SYMBOL",    v: runDetail.trade_proposal?.payload?.underlying_symbol ?? "—", c: "text-y" },
                        { l: "STRATEGY",  v: runDetail.trade_proposal?.payload?.strategy_type ?? "—",     c: "text-paper" },
                        { l: "NET DEBIT", v: `$${Number(runDetail.trade_proposal?.payload?.net_debit || 0).toFixed(2) ?? "0"}`, c: "text-warn" },
                        { l: "STATUS",    v: runDetail.trade_proposal?.payload?.accepted ? "ACCEPTED" : "REJECTED",
                          c: runDetail.trade_proposal?.payload?.accepted ? "text-pos" : "text-neg" },
                      ].map(({ l, v, c }) => (
                        <div key={l} className="px-3 py-2">
                          <div className="text-[8px] text-rule2 uppercase font-bold">{l}</div>
                          <div className={`font-bold mt-0.5 ${c}`}>{v}</div>
                        </div>
                      ))}
                    </div>
                  ),
                  jsonKey: "trade_proposal",
                },
                {
                  num: "03", label: "AI ANALYST + CRITIC EVENTS", show: (runDetail.agent_events?.length ?? 0) > 0,
                  icon: Brain, color: "#BF00FF",
                  body: () => (
                    <div className="divide-y-2 divide-rule2">
                      {runDetail.agent_events?.map((ev: any, i: number) => (
                        <div key={i} className="px-3 py-2.5">
                          <div className="flex items-center justify-between font-mono text-[10px]">
                            <span className="font-bold text-violet uppercase">{ev.event_type}</span>
                            <span className="text-rule2">{safeDate(ev.created_at, "time")}</span>
                          </div>
                          {ev.payload?.thesis   && <p className="text-[11px] text-muted italic mt-1">"{ev.payload.thesis}"</p>}
                          {ev.payload?.critique && <p className="text-[11px] text-muted mt-1">{ev.payload.critique}</p>}
                        </div>
                      ))}
                    </div>
                  ),
                  jsonKey: null,
                },
                {
                  num: "04", label: "DETERMINISTIC RISK GATE", show: !!runDetail.risk_check,
                  icon: ShieldCheck, color: "#FF8C00",
                  body: () => (
                    <div className={`font-mono text-[11px] font-bold px-3 py-2 ${
                      runDetail.risk_check?.approved ? "text-pos" : "text-neg"
                    }`}>
                      {runDetail.risk_check?.approved ? "ALL 18 GATES PASSED → APPROVED" : `BLOCKED: ${runDetail.risk_check?.payload?.blocking_reasons?.[0] ?? "Policy violation"}`}
                    </div>
                  ),
                  jsonKey: "risk_check",
                },
                {
                  num: "05", label: "ALPACA ORDER SUBMISSION", show: !!runDetail.order,
                  icon: Terminal, color: "#00FF41",
                  body: () => (
                    <div className="grid grid-cols-3 gap-0 divide-x-2 divide-rule2 font-mono text-[10px]">
                      {[
                        { l: "ORDER_ID", v: runDetail.order?.order_id ? `${runDetail.order.order_id.slice(0, 12)}…` : "—", c: "text-pos" },
                        { l: "CLIENT",   v: runDetail.order?.client_order_id ?? "—",        c: "text-paper" },
                        { l: "STATUS",   v: runDetail.order?.response_payload?.status ?? "submitted", c: "text-info" },
                      ].map(({ l, v, c }) => (
                        <div key={l} className="px-3 py-2">
                          <div className="text-[8px] text-rule2 uppercase font-bold">{l}</div>
                          <div className={`font-bold mt-0.5 truncate ${c}`}>{v}</div>
                        </div>
                      ))}
                    </div>
                  ),
                  jsonKey: "order",
                },
              ].filter(s => s.show).map(step => (
                <div key={step.num} className="bg-slab border-2" style={{ borderColor: step.color }}>
                  <div className="flex items-center justify-between px-3 py-2 border-b-2" style={{ borderBottomColor: step.color, background: "#000000" }}>
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-[9px]" style={{ color: step.color }}>{step.num}</span>
                      <step.icon className="w-3.5 h-3.5" style={{ color: step.color }} />
                      <span className="font-bold text-[10px] uppercase tracking-widest" style={{ color: step.color }}>{step.label}</span>
                    </div>
                    {step.jsonKey && (
                      <button
                        onClick={() => setInspectorData({ title: step.label, data: (runDetail as any)[step.jsonKey] })}
                        className="font-mono text-[9px] uppercase font-bold cursor-pointer hover:underline"
                        style={{ color: step.color }}
                      >
                        JSON
                      </button>
                    )}
                  </div>
                  {step.body()}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {inspectorData && (
        <Modal isOpen onClose={() => setInspectorData(null)} title={inspectorData.title}>
          <JsonViewer data={inspectorData.data} title={inspectorData.title} maxHeight="max-h-[60vh]" />
        </Modal>
      )}
    </div>
  );
};
