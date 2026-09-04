import React, { useEffect, useState } from "react";
import {
  Activity,
  CheckCircle,
  Clock,
  Layers,
  Play,
  RefreshCw,
  TrendingDown,
  TrendingUp,
  XCircle,
} from "lucide-react";
import { api } from "../api/client";
import { EmptyState }  from "../components/EmptyState";
import { JsonViewer }  from "../components/JsonViewer";
import { KpiCard }     from "../components/KpiCard";
import { Modal }       from "../components/Modal";
import { StatusBadge } from "../components/StatusBadge";
import { MonitorResponse, Order, Position } from "../types/api";

export const PositionsPage: React.FC = () => {
  const [positions,     setPositions]     = useState<Position[]>([]);
  const [orders,        setOrders]        = useState<Order[]>([]);
  const [loading,       setLoading]       = useState(true);
  const [syncing,       setSyncing]       = useState(false);
  const [errorMsg,      setErrorMsg]      = useState<string | null>(null);
  const [isMonitoring,  setIsMonitoring]  = useState(false);
  const [monitorResult, setMonitorResult] = useState<MonitorResponse | null>(null);
  const [monitorParams, setMonitorParams] = useState({
    sync_orders: true, cli_proof: true, execute_closes: false, dry_run: true,
  });
  const [inspectModal,  setInspectModal]  = useState<{ title: string; data: any } | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true); setErrorMsg(null);
      const [posRes, ordRes] = await Promise.allSettled([api.getPositions(), api.getOrders()]);
      if (posRes.status === "fulfilled") setPositions(posRes.value);
      if (ordRes.status === "fulfilled") setOrders(ordRes.value);
    } catch (e: any) { setErrorMsg(e.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchData(); }, []);

  const handleSyncOrders = async () => {
    try { setSyncing(true); await api.syncOrders(); await fetchData(); }
    catch (e: any) { setErrorMsg(e.message); }
    finally { setSyncing(false); }
  };

  const handleRunMonitor = async () => {
    try {
      setIsMonitoring(true); setErrorMsg(null);
      const res = await api.runMonitor(monitorParams);
      setMonitorResult(res);
      await fetchData();
    } catch (e: any) { setErrorMsg(e.message); }
    finally { setIsMonitoring(false); }
  };

  const totalMV    = positions.reduce((a, p) => a + (Number(p.market_value) || 0), 0);
  const totalCB    = positions.reduce((a, p) => a + (Number(p.cost_basis)   || 0), 0);
  const totalUPL   = positions.reduce((a, p) => a + (Number(p.unrealized_pl) || 0), 0);
  const totalUPLPc = totalCB > 0 ? (totalUPL / totalCB) * 100 : 0;
  const activeOrds = orders.filter(o => o.status === "new" || o.status === "partially_filled").length;

  const fmt = (v?: number) => v != null
    ? `$${v.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "—";

  return (
    <div className="space-y-4">

      {/* Header */}
      <div className="flex items-end justify-between">
        <div>
          <div className="text-[9px] font-bold uppercase tracking-widest text-muted">// MODULE</div>
          <h2 className="font-bold text-[20px] uppercase tracking-tight text-paper leading-tight">
            POSITIONS &amp; ORDERS
          </h2>
          <div className="text-[10px] text-muted mt-0.5 uppercase font-bold tracking-widest">
            LIVE PAPER PORTFOLIO — ALPACA BROKER RECONCILIATION
          </div>
        </div>
        <button
          onClick={fetchData}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-slab border-2 border-rule2 hover:border-rule font-mono font-bold text-[10px] uppercase text-muted hover:text-paper cursor-pointer disabled:opacity-40"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          REFRESH
        </button>
      </div>

      {/* KPI strip */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-0 border-2 border-rule shadow-hard-muted">
        <KpiCard label="Open Positions"  value={positions.length}   subtitle={`Cost basis: ${fmt(totalCB)}`} icon={Layers} />
        <KpiCard label="Portfolio MV"    value={fmt(totalMV)}        subtitle="Real-time option valuation"  icon={Activity} variant="cyan" />
        <KpiCard label="Unrealized P&L"  value={fmt(totalUPL)}       subtitle={`${totalUPLPc.toFixed(2)}% overall`}
          variant={totalUPL >= 0 ? "positive" : "negative"} icon={totalUPL >= 0 ? TrendingUp : TrendingDown}
          delta={`${totalUPL >= 0 ? "+" : ""}${totalUPLPc.toFixed(2)}%`} deltaPositive={totalUPL >= 0} />
        <KpiCard label="Active Orders"   value={activeOrds}          subtitle={`${orders.length} total`}    icon={Clock} />
      </div>

      {errorMsg && (
        <div className="bg-neg text-paper p-3 border-2 border-rule font-mono text-[11px] font-bold flex items-center justify-between">
          <span>ERR: {errorMsg}</span>
          <button onClick={() => setErrorMsg(null)} className="underline cursor-pointer">DISMISS</button>
        </div>
      )}

      {/* Monitor controller */}
      <div className="bg-slab border-2 border-info">
        <div className="flex flex-col lg:flex-row items-stretch border-b-2 border-info">
          <div className="flex items-center gap-2 px-4 py-3 bg-void border-b-2 lg:border-b-0 lg:border-r-2 border-info">
            <Activity className="w-4 h-4 text-info" />
            <span className="font-bold text-[11px] uppercase tracking-widest">POSITION MONITOR</span>
          </div>
          <div className="flex flex-wrap items-center gap-4 px-4 py-3 flex-1">
            {(["cli_proof", "execute_closes", "dry_run"] as const).map(key => (
              <label key={key} className="flex items-center gap-1.5 cursor-pointer font-mono text-[10px] font-bold uppercase text-muted">
                <input
                  type="checkbox"
                  checked={monitorParams[key]}
                  onChange={e => setMonitorParams({ ...monitorParams, [key]: e.target.checked })}
                  className="w-3.5 h-3.5 accent-info cursor-pointer"
                />
                {key.replace(/_/g, " ")}
              </label>
            ))}
          </div>
          <button
            onClick={handleRunMonitor}
            disabled={isMonitoring}
            className="flex items-center gap-2 px-5 py-3 bg-info text-ink font-mono font-bold text-[11px] uppercase tracking-widest hover:bg-info/80 disabled:opacity-40 cursor-pointer"
          >
            <Play className={`w-3.5 h-3.5 ${isMonitoring ? "animate-spin" : ""}`} />
            {isMonitoring ? "EVALUATING..." : "RUN MONITOR"}
          </button>
        </div>

        <div className="px-4 py-2 text-[9px] font-bold uppercase text-rule2">
          // EXIT RULES: TAKE-PROFIT +50% · STOP-LOSS -50% · TIME-STOP 14D · EXPIRY-RISK ≤3 DTE
        </div>

        {monitorResult && (
          <div className="border-t-2 border-rule2 p-4 space-y-3">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <span className="font-mono text-[11px] font-bold text-info uppercase">
                RUN: {monitorResult.run_id} · POSITIONS_CHECKED: {monitorResult.position_count}
              </span>
              <button
                onClick={() => setInspectModal({ title: "MONITOR RESULT", data: monitorResult })}
                className="font-mono text-[10px] text-muted hover:text-info underline cursor-pointer uppercase font-bold"
              >
                INSPECT JSON
              </button>
            </div>
            <div className="grid grid-cols-4 gap-2">
              {[
                { k: "held",            l: "HELD",        c: "#00FF41" },
                { k: "take_profit",     l: "TAKE PROFIT", c: "#FF8C00" },
                { k: "stop_loss",       l: "STOP LOSS",   c: "#FF003C" },
                { k: "expiration_risk", l: "EXPIRY RISK", c: "#666666" },
              ].map(({ k, l, c }) => (
                <div key={k} className="bg-ink border-2 border-rule2 p-2 text-center">
                  <div className="font-bold text-xl tabular-nums" style={{ color: c }}>
                    {(monitorResult.summary as any)?.[k] ?? 0}
                  </div>
                  <div className="text-[9px] font-bold text-rule2 mt-0.5">{l}</div>
                </div>
              ))}
            </div>
            {monitorResult.decisions?.length > 0 && (
              <div className="space-y-1">
                {monitorResult.decisions.map((dec: any, i: number) => (
                  <div key={i} className="flex items-center justify-between font-mono text-[10px] px-3 py-2 bg-ink border-2 border-rule2">
                    <div className="flex items-center gap-2 font-bold">
                      <span className="text-paper">{dec.symbol}</span>
                      <StatusBadge
                        variant={dec.action === "hold" ? "ok" : dec.should_close ? "danger" : "warn"}
                        size="sm"
                      >
                        {(dec.action ?? "—").toUpperCase()}
                      </StatusBadge>
                      <span className="text-muted font-normal">{dec.reason}</span>
                    </div>
                    <span className="text-rule2">PRI:{dec.priority}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Positions table */}
      <div className="bg-slab border-2 border-rule">
        <div className="flex items-center justify-between px-4 py-2.5 border-b-2 border-rule bg-ink">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-paper" />
            <span className="font-bold text-[11px] uppercase tracking-widest">ACTIVE PAPER POSITIONS</span>
          </div>
        </div>

        {positions.length === 0 ? (
          <EmptyState
            icon={Layers}
            title="No open positions"
            description="Execute a trade from the Cockpit to open a paper options position."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-[11px] font-mono">
              <thead>
                <tr className="bg-ink border-b-2 border-rule2">
                  {["SYMBOL", "SIDE/QTY", "ENTRY", "CURRENT", "COST BASIS", "MKT VALUE", "UNREAL P&L", "BAR"].map(h => (
                    <th key={h} className="px-3 py-2 text-[9px] font-bold uppercase tracking-widest text-muted text-left">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y-2 divide-rule2">
                {positions.map(pos => {
                  const isPos = Number(pos.unrealized_pl) >= 0;
                  const plPct = (Number(pos.unrealized_plpc) || 0) * 100;
                  const barW  = Math.min(Math.abs(plPct) * 2, 100);
                  return (
                    <tr key={pos.asset_id || pos.symbol} className="hover:bg-rule2">
                      <td className="px-3 py-3">
                        <div className="font-bold text-[13px] text-paper">{pos.symbol}</div>
                        <div className="text-[9px] text-rule2 uppercase">{pos.asset_class}</div>
                      </td>
                      <td className="px-3 py-3">
                        <span className={`font-bold text-[10px] uppercase mr-1.5 ${pos.side === "long" ? "text-pos" : "text-neg"}`}>
                          {pos.side}
                        </span>
                        <span className="text-paper">{pos.qty}</span>
                      </td>
                      <td className="px-3 py-3 text-muted tabular-nums">
                        {pos.avg_entry_price != null ? `$${Number(pos.avg_entry_price).toFixed(2)}` : "—"}
                      </td>
                      <td className="px-3 py-3 font-bold text-paper tabular-nums">
                        {pos.current_price != null ? `$${Number(pos.current_price).toFixed(2)}` : "—"}
                      </td>
                      <td className="px-3 py-3 text-muted tabular-nums">
                        {pos.cost_basis != null ? `$${Number(pos.cost_basis).toFixed(2)}` : "—"}
                      </td>
                      <td className="px-3 py-3 font-bold text-info tabular-nums">
                        {pos.market_value != null ? `$${Number(pos.market_value).toFixed(2)}` : "—"}
                      </td>
                      <td className={`px-3 py-3 font-bold tabular-nums ${isPos ? "text-pos" : "text-neg"}`}>
                        {isPos ? "+" : ""}{(Number(pos.unrealized_pl) || 0).toFixed(2)}
                        <div className="text-[9px] opacity-70">{isPos ? "+" : ""}{plPct.toFixed(2)}%</div>
                      </td>
                      <td className="px-3 py-3 w-16">
                        <div className="w-14 h-2 bg-rule2 border border-rule2">
                          <div
                            className={`h-full ${isPos ? "bg-pos" : "bg-neg"}`}
                            style={{ width: `${barW}%` }}
                          />
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Orders table */}
      <div className="bg-slab border-2 border-rule2">
        <div className="flex items-center justify-between px-4 py-2.5 border-b-2 border-rule2 bg-ink">
          <div>
            <span className="font-bold text-[11px] uppercase tracking-widest text-paper">ORDER HISTORY</span>
            <span className="ml-3 text-[9px] font-bold uppercase text-rule2">// RECONCILED WITH ALPACA API</span>
          </div>
          <button
            onClick={handleSyncOrders}
            disabled={syncing}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-ink border-2 border-rule2 hover:border-rule font-mono font-bold text-[10px] uppercase text-muted hover:text-paper cursor-pointer disabled:opacity-40"
          >
            <RefreshCw className={`w-3 h-3 ${syncing ? "animate-spin" : ""}`} />
            SYNC ORDERS
          </button>
        </div>

        {orders.length === 0 ? (
          <EmptyState icon={Clock} title="No orders found" description="Submitted orders appear here with fill status and timestamps." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-[11px] font-mono">
              <thead>
                <tr className="bg-ink border-b-2 border-rule2">
                  {["ORDER_ID", "SYMBOL", "SIDE/QTY", "TYPE", "STATUS", "FILL AVG", "SUBMITTED"].map(h => (
                    <th key={h} className="px-3 py-2 text-[9px] font-bold uppercase tracking-widest text-muted text-left">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y-2 divide-rule2">
                {orders.map(ord => (
                  <tr key={ord.id} className="hover:bg-rule2">
                    <td className="px-3 py-3">
                      <div className="text-info font-bold truncate max-w-[120px]" title={ord.id}>
                        {(ord.id ?? "").slice(0, 8)}…
                      </div>
                      <div className="text-[9px] text-rule2 truncate">{ord.client_order_id || "—"}</div>
                    </td>
                    <td className="px-3 py-3 font-bold text-paper">{ord.symbol}</td>
                    <td className="px-3 py-3">
                      <span className={`font-bold uppercase mr-1.5 ${ord.side === "buy" ? "text-pos" : "text-neg"}`}>{ord.side}</span>
                      {ord.qty}
                    </td>
                    <td className="px-3 py-3 text-muted uppercase">{ord.order_type || ord.type || "limit"}</td>
                    <td className="px-3 py-3">
                      <StatusBadge
                        variant={
                          ord.status === "filled" ? "ok" :
                          ord.status === "canceled" || ord.status === "rejected" ? "danger" : "warn"
                        }
                        size="sm"
                      >
                        {(ord.status ?? "unknown").toUpperCase()}
                      </StatusBadge>
                    </td>
                    <td className="px-3 py-3 font-bold text-paper tabular-nums">
                      {ord.filled_avg_price ? `$${Number(ord.filled_avg_price).toFixed(2)}` : "—"}
                    </td>
                    <td className="px-3 py-3 text-rule2 text-[10px]">
                      {ord.created_at ? new Date(ord.created_at).toLocaleString() : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {inspectModal && (
        <Modal isOpen onClose={() => setInspectModal(null)} title={inspectModal.title}>
          <JsonViewer data={inspectModal.data} title={inspectModal.title} />
        </Modal>
      )}
    </div>
  );
};
