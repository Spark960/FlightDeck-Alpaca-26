import React, { useEffect, useState } from "react";
import {
  ArrowDownRight,
  ArrowUpRight,
  Bot,
  Brain,
  CheckCircle,
  Crosshair,
  FileCode,
  Layers,
  RefreshCw,
  Send,
  ShieldAlert,
  ShieldCheck,
  XCircle,
  Zap,
} from "lucide-react";
import { api } from "../api/client";
import {
  ExecuteTradeResponse,
  MarketCandidate,
  ProposalReviewResponse,
  RiskCheckResponse,
  TradeProposal,
} from "../types/api";
import { EmptyState }  from "../components/EmptyState";
import { JsonViewer }  from "../components/JsonViewer";
import { Modal }       from "../components/Modal";
import { StatusBadge } from "../components/StatusBadge";

// ── Step pipeline bar ──────────────────────────────────────────────────────
const STEPS = ["01_SCAN", "02_PROPOSE", "03_AI_REVIEW", "04_RISK_GATE", "05_EXECUTE"];

const StepBar: React.FC<{ activeIndex: number }> = ({ activeIndex }) => (
  <div className="flex items-stretch border-2 border-rule2 w-full overflow-hidden">
    {STEPS.map((step, i) => {
      const done    = i < activeIndex;
      const current = i === activeIndex;
      return (
        <div
          key={step}
          className={`flex-1 flex items-center justify-center px-2 py-2 text-[9px] font-bold border-r-2 border-rule2 last:border-r-0 ${
            current ? "bg-y text-ink" :
            done    ? "bg-pos text-ink" :
                      "bg-slab text-rule2"
          }`}
        >
          {current && <span className="blink mr-1">▶</span>}
          {done    && <span className="mr-1">✓</span>}
          {step}
        </div>
      );
    })}
  </div>
);

// ── Main Page ──────────────────────────────────────────────────────────────
export const CockpitPage: React.FC = () => {
  const [candidates,        setCandidates]        = useState<MarketCandidate[]>([]);
  const [isScanning,        setIsScanning]        = useState(false);
  const [proposal,          setProposal]          = useState<TradeProposal | null>(null);
  const [isProposing,       setIsProposing]       = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState<MarketCandidate | null>(null);
  const [review,            setReview]            = useState<ProposalReviewResponse | null>(null);
  const [isReviewing,       setIsReviewing]       = useState(false);
  const [riskCheck,         setRiskCheck]         = useState<RiskCheckResponse | null>(null);
  const [isCheckingRisk,    setIsCheckingRisk]    = useState(false);
  const [executeResult,     setExecuteResult]     = useState<ExecuteTradeResponse | null>(null);
  const [isExecuting,       setIsExecuting]       = useState(false);
  const [dryRunMode,        setDryRunMode]        = useState(true);
  const [isCycleRunning,    setIsCycleRunning]    = useState(false);
  const [cycleLog,          setCycleLog]          = useState<string[]>([]);
  const [inspectorData,     setInspectorData]     = useState<{ title: string; data: any } | null>(null);
  const [errorMsg,          setErrorMsg]          = useState<string | null>(null);

  const activeStep =
    executeResult ? 4 :
    riskCheck     ? 3 :
    review        ? 2 :
    proposal?.accepted ? 1 :
    0;

  const logLine = (msg: string) => setCycleLog(prev => [...prev.slice(-5), msg]);

  const handleScan = async () => {
    try {
      setIsScanning(true); setErrorMsg(null);
      const res = await api.scanMarket(undefined, 6);
      setCandidates(res.candidates);
      const top = res.candidates.find(c => c.direction !== "none");
      if (top) setSelectedCandidate(top);
    } catch (err: any) { setErrorMsg(`SCAN ERR: ${err.message}`); }
    finally { setIsScanning(false); }
  };

  useEffect(() => { handleScan(); }, []);

  const handleGenerateProposal = async (candidate: MarketCandidate) => {
    try {
      setIsProposing(true); setErrorMsg(null);
      setSelectedCandidate(candidate);
      setProposal(null); setReview(null); setRiskCheck(null); setExecuteResult(null);
      const dir = candidate.direction === "bearish" ? "bearish" : "bullish";
      const p = await api.createProposal(candidate.symbol, dir, 1500);
      setProposal(p);
      if (p.accepted) await handleReviewAndRisk(p, candidate);
    } catch (err: any) { setErrorMsg(`PROPOSE ERR: ${err.message}`); }
    finally { setIsProposing(false); }
  };

  const handleReviewAndRisk = async (p: TradeProposal, cand?: MarketCandidate) => {
    try {
      setIsReviewing(true); setIsCheckingRisk(true); setErrorMsg(null);
      const rev = await api.reviewProposal({ proposal: p, proposal_id: p.proposal_id, market_candidate: cand || selectedCandidate });
      setReview(rev);
      const risk = await api.checkRisk({ proposal: p, proposal_id: p.proposal_id });
      setRiskCheck(risk);
    } catch (err: any) { setErrorMsg(`REVIEW ERR: ${err.message}`); }
    finally { setIsReviewing(false); setIsCheckingRisk(false); }
  };

  const handleExecute = async () => {
    if (!proposal?.proposal_id) return;
    try {
      setIsExecuting(true); setErrorMsg(null);
      const res = await api.executeTrade(proposal.proposal_id, dryRunMode);
      setExecuteResult(res);
    } catch (err: any) { setErrorMsg(`EXEC ERR: ${err.message}`); }
    finally { setIsExecuting(false); }
  };

  const handleRunFullCycle = async () => {
    try {
      setIsCycleRunning(true); setErrorMsg(null);
      setCycleLog([]); setExecuteResult(null);

      logLine("[01/05] SCANNING 11 LIQUID UNDERLYINGS...");
      const scan = await api.scanMarket(undefined, 5);
      setCandidates(scan.candidates);
      const top = scan.candidates.find(c => c.direction !== "none") || scan.candidates[0];
      if (!top) throw new Error("NO TRADEABLE CANDIDATE IN UNIVERSE");
      setSelectedCandidate(top);
      logLine(`[01/05] TOP SIGNAL: ${top.symbol} ${top.direction.toUpperCase()}`);

      logLine(`[02/05] BUILDING DEBIT SPREAD: ${top.symbol}...`);
      const dir = top.direction === "bearish" ? "bearish" : "bullish";
      const p = await api.createProposal(top.symbol, dir, 1500);
      setProposal(p);
      if (!p.accepted) { logLine(`[02/05] SELECTOR REJECTED: ${p.rejection_reason || p.rejection_reasons?.[0] || "NO LIQUID STRIKES"}`); return; }
      logLine(`[02/05] ACCEPTED: ${p.strategy_type} NET_DEBIT=$${Number(p.net_debit || 0).toFixed(2)}`);

      logLine("[03/05] AI ANALYST + CRITIC REVIEW...");
      const rev = await api.reviewProposal({ proposal: p, proposal_id: p.proposal_id, market_candidate: top });
      setReview(rev);
      logLine(`[03/05] VERDICT: ${(rev.critic.verdict ?? "unknown").toUpperCase()}`);

      logLine("[04/05] EVALUATING 18 RISK GATES...");
      const risk = await api.checkRisk({ proposal: p, proposal_id: p.proposal_id });
      setRiskCheck(risk);
      logLine(`[04/05] RISK: ${risk.approved ? "ALL GATES PASSED" : "BLOCKED: " + risk.blocking_reasons[0]}`);

      if (!p.proposal_id) throw new Error("NO PROPOSAL ID");
      logLine(`[05/05] ROUTING ORDER (${dryRunMode ? "DRY-RUN" : "PAPER"})...`);
      const exec = await api.executeTrade(p.proposal_id, dryRunMode);
      setExecuteResult(exec);
      logLine(`[05/05] ${exec.risk_approved ? "ORDER SUBMITTED" : "BLOCKED BY RISK GATE"}`);
    } catch (err: any) {
      setErrorMsg(`CYCLE ABORTED: ${err.message}`);
      logLine(`[ERR] ${err.message}`);
    } finally {
      setIsCycleRunning(false);
    }
  };

  return (
    <div className="space-y-4">

      {/* ── MISSION CONTROL HEADER ────────────────────────── */}
      <div className="bg-slab border-2 border-rule shadow-hard-y">
        <div className="flex items-center justify-between px-4 py-3 border-b-2 border-rule">
          <div className="flex items-center gap-3">
            <Bot className="w-5 h-5 text-y" />
            <div>
              <div className="font-bold text-[13px] uppercase tracking-widest text-paper">
                AUTONOMOUS MISSION CONTROL
              </div>
              <div className="text-[9px] text-muted mt-0.5">
                SCAN → PROPOSE → AI_REVIEW → RISK_GATE → ALPACA_PAPER_ORDER
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <StatusBadge variant="ok" pulse>LIVE</StatusBadge>
            <StatusBadge variant="yellow">{dryRunMode ? "DRY-RUN" : "PAPER"}</StatusBadge>
          </div>
        </div>

        <StepBar activeIndex={activeStep} />

        {/* CTA row */}
        <div className="flex flex-wrap items-center gap-3 px-4 py-3">
          <button
            onClick={handleRunFullCycle}
            disabled={isCycleRunning}
            className="flex items-center gap-2 px-5 py-2.5 bg-y text-ink font-bold text-[11px] uppercase tracking-widest border-2 border-y hover:bg-ink hover:text-y disabled:opacity-40 cursor-pointer shadow-hard-sm"
          >
            <Zap className="w-4 h-4" />
            {isCycleRunning ? "EXECUTING..." : "RUN AUTONOMOUS CYCLE"}
          </button>
          <button
            onClick={handleScan}
            disabled={isScanning || isCycleRunning}
            className="flex items-center gap-2 px-4 py-2.5 bg-slab text-paper font-bold text-[11px] uppercase tracking-widest border-2 border-rule2 hover:border-rule disabled:opacity-40 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isScanning ? "animate-spin" : ""}`} />
            RESCAN
          </button>
          <label className="flex items-center gap-2 cursor-pointer text-[11px] font-bold uppercase text-muted ml-auto">
            <input
              type="checkbox"
              checked={dryRunMode}
              onChange={e => setDryRunMode(e.target.checked)}
              className="w-4 h-4 accent-y cursor-pointer"
            />
            DRY-RUN MODE
          </label>
        </div>

        {/* Cycle log terminal */}
        {cycleLog.length > 0 && (
          <div className="border-t-2 border-rule2 bg-ink px-4 py-3">
            {cycleLog.map((line, i) => (
              <div key={i} className="font-mono text-[10px] text-pos leading-5">
                {i === cycleLog.length - 1 ? <span className="blink">▶ </span> : <span className="text-rule2">  </span>}
                {line}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Error */}
      {errorMsg && (
        <div className="bg-neg text-paper p-3 border-2 border-rule font-mono text-[11px] font-bold flex items-center justify-between">
          <span>{errorMsg}</span>
          <button onClick={() => setErrorMsg(null)} className="underline cursor-pointer">DISMISS</button>
        </div>
      )}

      {/* ── GRID: Scanner + Proposal ─────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">

        {/* Scanner */}
        <div className="lg:col-span-5">
          <div className="bg-slab border-2 border-rule h-full flex flex-col">
            <div className="flex items-center justify-between px-4 py-2.5 border-b-2 border-rule bg-ink">
              <div className="flex items-center gap-2">
                <Crosshair className="w-4 h-4 text-y" />
                <span className="font-bold text-[11px] uppercase tracking-widest">LIQUID UNIVERSE SCANNER</span>
              </div>
              <button
                onClick={handleScan}
                disabled={isScanning}
                className="text-muted hover:text-y cursor-pointer font-mono text-[10px] font-bold uppercase"
              >
                {isScanning ? "SCANNING..." : "REFRESH"}
              </button>
            </div>

            {candidates.length === 0 ? (
              <div className="flex-1">
                <EmptyState
                  icon={Crosshair}
                  title="No scan results"
                  description="Scan the 11-symbol liquid universe to rank momentum signals."
                  actionLabel="Run Scanner"
                  onAction={handleScan}
                  isLoading={isScanning}
                />
              </div>
            ) : (
              <>
                {/* Table header */}
                <div className="grid grid-cols-12 gap-0 px-3 py-1.5 bg-ink border-b-2 border-rule2">
                  {["SYMBOL", "DIR", "SCORE", "1D%", "VOL"].map((h, i) => (
                    <div key={h} className={`font-bold text-[9px] uppercase tracking-widest text-muted ${
                      i === 0 ? "col-span-3" : i <= 2 ? "col-span-2" : "col-span-2 text-right"
                    } ${i === 4 ? "col-span-3 text-right" : ""}`}>{h}</div>
                  ))}
                </div>

                <div className="flex-1 divide-y-2 divide-rule2 overflow-y-auto">
                  {candidates.map((cand) => {
                    const sel  = selectedCandidate?.symbol === cand.symbol;
                    const bull = cand.direction === "bullish";
                    const bear = cand.direction === "bearish";
                    return (
                      <div
                        key={cand.symbol}
                        onClick={() => handleGenerateProposal(cand)}
                        className={`grid grid-cols-12 gap-0 items-center px-3 py-3 cursor-pointer ${
                          sel ? "bg-y text-ink" : "hover:bg-rule2 text-paper"
                        }`}
                      >
                        <div className="col-span-3">
                          <div className={`font-bold text-[13px] ${sel ? "text-ink" : ""}`}>{cand.symbol}</div>
                          <div className={`text-[9px] tabular-nums ${sel ? "text-rule2" : "text-muted"}`}>
                            {cand.features?.last_price != null ? `$${Number(cand.features.last_price).toFixed(2)}` : "—"}
                          </div>
                        </div>
                        <div className="col-span-2">
                          <span className={`font-bold text-[9px] uppercase flex items-center gap-0.5 ${
                            bull ? (sel ? "text-[#006600]" : "text-pos") :
                            bear ? (sel ? "text-[#880000]" : "text-neg") :
                            "text-muted"
                          }`}>
                            {bull && <ArrowUpRight className="w-3 h-3" />}
                            {bear && <ArrowDownRight className="w-3 h-3" />}
                            {(cand.direction ?? "none").toUpperCase().slice(0,4)}
                          </span>
                        </div>
                        <div className={`col-span-2 font-bold text-[11px] tabular-nums ${sel ? "text-ink" : "text-paper"}`}>
                          {cand.best_score != null ? Number(cand.best_score).toFixed(2) : "—"}
                        </div>
                        <div className={`col-span-2 text-right font-bold text-[11px] tabular-nums ${
                          (cand.features?.one_day_return_pct ?? 0) >= 0
                            ? (sel ? "text-[#006600]" : "text-pos")
                            : (sel ? "text-[#880000]" : "text-neg")
                        }`}>
                          {cand.features?.one_day_return_pct != null ? Number(cand.features.one_day_return_pct).toFixed(2) + "%" : "—"}
                        </div>
                        <div className={`col-span-3 text-right text-[10px] tabular-nums ${sel ? "text-muted" : "text-muted"}`}>
                          {cand.features?.volume_ratio != null ? Number(cand.features.volume_ratio).toFixed(2) : "1.0"}x
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div className="px-3 py-1.5 border-t-2 border-rule2 bg-ink text-[9px] text-rule2 font-bold uppercase">
                  // CLICK ROW TO BUILD DEBIT SPREAD
                </div>
              </>
            )}
          </div>
        </div>

        {/* Proposal + AI + Risk + Execute */}
        <div className="lg:col-span-7 space-y-4">

          {/* Proposal */}
          <div className="bg-slab border-2 border-rule">
            <div className="flex items-center justify-between px-4 py-2.5 border-b-2 border-rule bg-ink">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-violet" />
                <span className="font-bold text-[11px] uppercase tracking-widest">TRADE PROPOSAL</span>
              </div>
              <div className="flex items-center gap-2">
                {proposal?.accepted   && <StatusBadge variant="ok"     size="sm">ACCEPTED</StatusBadge>}
                {proposal && !proposal.accepted && <StatusBadge variant="danger" size="sm">REJECTED</StatusBadge>}
                {isProposing           && <StatusBadge variant="info"   size="sm" pulse>BUILDING</StatusBadge>}
                {proposal && (
                  <button onClick={() => setInspectorData({ title: "PROPOSAL", data: proposal })}
                    className="font-mono text-[9px] text-muted hover:text-y uppercase font-bold cursor-pointer flex items-center gap-1">
                    <FileCode className="w-3 h-3" />JSON
                  </button>
                )}
              </div>
            </div>

            {!proposal ? (
              <EmptyState
                icon={Layers}
                title="Awaiting proposal"
                description={selectedCandidate
                  ? `Select a row or run cycle to build a spread for ${selectedCandidate.symbol}`
                  : "Select a candidate from the scanner"}
                actionLabel={selectedCandidate ? `PROPOSE ${selectedCandidate.symbol}` : "SCAN"}
                onAction={() => selectedCandidate ? handleGenerateProposal(selectedCandidate) : handleScan()}
                isLoading={isProposing}
              />
            ) : !proposal.accepted ? (
              <div className="p-4 flex items-start gap-2 font-mono text-[11px] text-neg font-bold border-l-4 border-neg bg-[#0A0000] m-4">
                <XCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <div>
                  SELECTOR REJECTED: {proposal.rejection_reason || proposal.rejection_reasons?.[0] || "NO LIQUID STRIKES MET CRITERIA"}
                </div>
              </div>
            ) : (
              <div>
                {/* Summary row */}
                <div className="grid grid-cols-2 sm:grid-cols-5 border-b-2 border-rule2 divide-x-2 divide-rule2">
                  {[
                    { l: "STRATEGY", v: proposal.strategy_type.replace(/_/g," ").toUpperCase(), c: "text-paper" },
                    { l: "SYMBOL",   v: proposal.underlying_symbol, c: "text-y" },
                    { l: "EXPIRY",   v: proposal.expiration,        c: "text-muted" },
                    { l: "NET DEBIT",v: `$${Number(proposal.net_debit || 0).toFixed(2) ?? "0.00"}`, c: "text-warn" },
                    { l: "MAX LOSS", v: `$${Number(proposal.max_loss || 0).toFixed(2) ?? "0.00"}`, c: "text-neg" },
                  ].map(({ l, v, c }) => (
                    <div key={l} className="px-3 py-2.5">
                      <div className="text-[8px] font-bold uppercase tracking-widest text-muted">{l}</div>
                      <div className={`font-bold text-[11px] mt-0.5 tabular-nums ${c}`}>{v}</div>
                    </div>
                  ))}
                </div>

                {/* Legs table */}
                <table className="w-full text-[11px]">
                  <thead>
                    <tr className="bg-ink border-b-2 border-rule2">
                      {["ACTION", "STRIKE", "TYPE", "BID", "ASK", "MID", "DELTA"].map(h => (
                        <th key={h} className={`px-3 py-2 text-[8px] font-bold uppercase tracking-widest text-muted ${
                          h === "BID" || h === "ASK" || h === "MID" || h === "DELTA" ? "text-right" : "text-left"
                        }`}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="font-mono divide-y-2 divide-rule2">
                    {proposal.legs.map((leg, idx) => (
                      <tr key={idx} className="hover:bg-rule2">
                        <td className="px-3 py-2">
                          <span className={`font-bold text-[10px] uppercase ${leg.side === "buy" ? "text-pos" : "text-neg"}`}>
                            {leg.side.toUpperCase()}
                          </span>
                        </td>
                        <td className="px-3 py-2 font-bold text-paper tabular-nums">
                          {leg.strike != null ? `$${leg.strike}` : "—"}
                        </td>
                        <td className="px-3 py-2 text-muted uppercase">{leg.type}</td>
                        <td className="px-3 py-2 text-right text-muted tabular-nums">
                          {leg.bid != null ? `$${Number(leg.bid).toFixed(2)}` : "—"}
                        </td>
                        <td className="px-3 py-2 text-right text-muted tabular-nums">
                          {leg.ask != null ? `$${Number(leg.ask).toFixed(2)}` : "—"}
                        </td>
                        <td className="px-3 py-2 text-right font-bold text-info tabular-nums">
                          {leg.mid != null ? `$${Number(leg.mid).toFixed(2)}` : "—"}
                        </td>
                        <td className="px-3 py-2 text-right text-muted tabular-nums">
                          {leg.delta != null ? Number(leg.delta).toFixed(3) : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* AI Panels */}
          {(proposal?.accepted || isReviewing) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

              {/* Analyst */}
              <div className="bg-slab border-2 border-violet">
                <div className="flex items-center justify-between px-3 py-2 border-b-2 border-violet bg-[#0A0010]">
                  <div className="flex items-center gap-1.5">
                    <Brain className="w-3.5 h-3.5 text-violet" />
                    <span className="font-bold text-[10px] uppercase tracking-widest">AI ANALYST</span>
                  </div>
                  {review && (
                    <span className="font-mono text-[9px] font-bold text-violet">
                      CONF: {(Number(review.analyst.confidence) * 100).toFixed(0)}%
                    </span>
                  )}
                </div>
                <div className="p-3 font-mono text-[11px] min-h-[80px]">
                  {isReviewing ? (
                    <span className="text-rule2 font-bold uppercase">
                      <span className="blink">▶</span> SYNTHESIZING THESIS...
                    </span>
                  ) : review ? (
                    <div className="space-y-2">
                      <p className="text-[#AAAAAA] leading-relaxed italic">
                        "{review.analyst.thesis}"
                      </p>
                      <div className="text-[9px] text-muted space-y-0.5 uppercase">
                        <div>REGIME: {review.analyst.market_regime}</div>
                        {review.analyst.invalidation_condition && (
                          <div className="text-warn">INVALIDATION: {review.analyst.invalidation_condition}</div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <button
                      onClick={() => proposal && handleReviewAndRisk(proposal)}
                      className="font-bold text-[10px] text-violet hover:underline cursor-pointer uppercase"
                    >
                      &gt; REQUEST AI REVIEW
                    </button>
                  )}
                </div>
              </div>

              {/* Critic */}
              <div className={`bg-slab border-2 ${
                review
                  ? (review.critic.passed ? "border-pos" : "border-neg")
                  : "border-rule2"
              }`}>
                <div className={`flex items-center justify-between px-3 py-2 border-b-2 ${
                  review
                    ? (review.critic.passed ? "border-pos bg-[#001a00]" : "border-neg bg-[#1a0000]")
                    : "border-rule2 bg-ink"
                }`}>
                  <div className="flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5" style={{
                      color: review ? (review.critic.passed ? "#00FF41" : "#FF003C") : "#333333"
                    }} />
                    <span className="font-bold text-[10px] uppercase tracking-widest">AI CRITIC</span>
                  </div>
                  {review && (
                    <StatusBadge variant={review.critic.passed ? "ok" : "danger"} size="sm">
                      {(review.critic.verdict ?? "unknown").toUpperCase()}
                    </StatusBadge>
                  )}
                </div>
                <div className="p-3 font-mono text-[11px] min-h-[80px]">
                  {isReviewing ? (
                    <span className="text-rule2 font-bold uppercase">
                      <span className="blink">▶</span> VALIDATING LOGIC...
                    </span>
                  ) : review ? (
                    <p className="text-[#AAAAAA] leading-relaxed">
                      {review.critic.critique || "THESIS PASSED ALL VALIDATION CHECKS."}
                    </p>
                  ) : (
                    <span className="text-rule2 text-[10px] uppercase font-bold">AWAITING ANALYST...</span>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Risk Gate */}
          {(riskCheck || isCheckingRisk) && (
            <div className={`bg-slab border-2 ${
              riskCheck
                ? (riskCheck.approved ? "border-pos" : "border-neg")
                : "border-warn"
            }`}>
              <div className={`flex items-center justify-between px-4 py-2.5 border-b-2 ${
                riskCheck
                  ? (riskCheck.approved ? "border-pos bg-[#001a00]" : "border-neg bg-[#1a0000]")
                  : "border-warn bg-[#0A0A00]"
              }`}>
                <div className="flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-warn" />
                  <span className="font-bold text-[11px] uppercase tracking-widest">18-GATE RISK EVALUATION</span>
                </div>
                {riskCheck && (
                  <StatusBadge variant={riskCheck.approved ? "ok" : "danger"} pulse={riskCheck.approved}>
                    {riskCheck.approved ? "ALL GATES PASSED" : "BLOCKED"}
                  </StatusBadge>
                )}
              </div>
              <div className="px-4 py-3 font-mono text-[11px]">
                {isCheckingRisk ? (
                  <span className="text-muted font-bold uppercase"><span className="blink">▶</span> AUDITING 18 DETERMINISTIC RULES...</span>
                ) : riskCheck?.approved ? (
                  <div className="flex items-start gap-2 text-pos font-bold">
                    <CheckCircle className="w-4 h-4 shrink-0 mt-0.5" />
                    ALL RISK LIMITS SATISFIED. MAX_LOSS=${riskCheck.computed_risk?.max_loss} ({riskCheck.computed_risk?.risk_pct_of_equity}% EQ)
                  </div>
                ) : riskCheck ? (
                  <div>
                    <div className="flex items-center gap-1.5 text-neg font-bold mb-2">
                      <XCircle className="w-4 h-4 shrink-0" />
                      BLOCKING POLICIES:
                    </div>
                    <ul className="list-none space-y-0.5">
                      {riskCheck.blocking_reasons.map((r, i) => (
                        <li key={i} className="text-warn before:content-['→'] before:mr-1.5">{r}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </div>
            </div>
          )}

          {/* Execute */}
          {proposal?.accepted && (
            <div className="bg-slab border-2 border-rule2">
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-0 border-b-2 border-rule2">
                <div className="flex-1 px-4 py-3 border-b-2 sm:border-b-0 sm:border-r-2 border-rule2">
                  <label className="flex items-center gap-2 cursor-pointer font-mono text-[10px] font-bold uppercase text-muted">
                    <input
                      type="checkbox"
                      checked={dryRunMode}
                      onChange={e => setDryRunMode(e.target.checked)}
                      className="w-4 h-4 accent-y cursor-pointer"
                    />
                    DRY-RUN MODE
                    <span className="text-rule2 normal-case font-normal ml-1">
                      {dryRunMode ? "(simulates gate, no order)" : "(submits to Alpaca paper)"}
                    </span>
                  </label>
                </div>
                <button
                  onClick={handleExecute}
                  disabled={isExecuting || !proposal.accepted}
                  className={`flex items-center justify-center gap-2 px-6 py-3 font-mono font-bold text-[11px] uppercase tracking-widest border-0 disabled:opacity-40 cursor-pointer ${
                    dryRunMode
                      ? "bg-info text-ink hover:bg-info/80"
                      : "bg-pos text-ink hover:bg-[#00CC33]"
                  }`}
                  style={{ boxShadow: dryRunMode ? "none" : "3px 3px 0 #FFFFFF" }}
                >
                  <Send className="w-3.5 h-3.5" />
                  {isExecuting ? "ROUTING..." : dryRunMode ? "DRY-RUN EXECUTION" : "SUBMIT PAPER ORDER"}
                </button>
              </div>

              {executeResult && (
                <div className={`p-4 font-mono text-[11px] font-bold border-t-2 ${
                  executeResult.risk_approved
                    ? "bg-[#001a00] border-pos text-pos"
                    : "bg-[#1a0000] border-neg text-neg"
                }`}>
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-1.5">
                      {executeResult.risk_approved ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                      {executeResult.dry_run ? "DRY-RUN VALIDATED" : executeResult.risk_approved ? "ORDER ROUTED TO ALPACA" : "ORDER BLOCKED"}
                    </div>
                    <button
                      onClick={() => setInspectorData({ title: "EXEC RESULT", data: executeResult })}
                      className="text-[10px] underline cursor-pointer opacity-60 hover:opacity-100"
                    >
                      INSPECT JSON
                    </button>
                  </div>
                  <div className="mt-1 text-[10px] opacity-60">
                    RUN_ID: {executeResult.run_id}
                  </div>
                  {executeResult.order_id && (
                    <div className="mt-0.5">ORDER_ID: {executeResult.order_id}</div>
                  )}
                  {(executeResult.blocking_reasons?.length ?? 0) > 0 && (
                    <div className="mt-1 text-warn">
                      REASONS: {executeResult.blocking_reasons?.join(", ")}
                    </div>
                  )}
                </div>
              )}
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
