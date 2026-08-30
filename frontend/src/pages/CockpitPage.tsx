import { useCallback, useEffect, useState } from "react";

import { api } from "../api/client";
import { Card } from "../components/Card";
import { ErrorState, LoadingState } from "../components/StateViews";
import { StatusBadge } from "../components/StatusBadge";

function money(value: string | number | undefined) {
  const amount = Number(value ?? 0);
  return amount.toLocaleString(undefined, { style: "currency", currency: "USD" });
}

export function CockpitPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [account, setAccount] = useState<Record<string, string> | null>(null);
  const [positions, setPositions] = useState<Array<Record<string, string>>>([]);
  const [orders, setOrders] = useState<Array<Record<string, string>>>([]);
  const [clock, setClock] = useState<Record<string, unknown> | null>(null);
  const [runs, setRuns] = useState<Awaited<ReturnType<typeof api.auditRuns>>>([]);
  const [monitor, setMonitor] = useState<Awaited<ReturnType<typeof api.monitorLatest>> | null>(null);
  const [scanning, setScanning] = useState(false);
  const [lastScan, setLastScan] = useState<Record<string, unknown> | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [accountData, positionData, orderData, clockData, runData, monitorData] = await Promise.all([
        api.account(),
        api.positions(),
        api.orders(),
        api.clock(),
        api.auditRuns(12),
        api.monitorLatest(),
      ]);
      setAccount(accountData);
      setPositions(positionData);
      setOrders(orderData);
      setClock(clockData);
      setRuns(runData);
      setMonitor(monitorData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load cockpit data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const runScan = async () => {
    setScanning(true);
    try {
      const result = await api.scan(5);
      setLastScan(result);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Scan failed");
    } finally {
      setScanning(false);
    }
  };

  if (loading) return <LoadingState title="Cockpit" message="Loading account, positions, and audit trail…" />;
  if (error) return <ErrorState title="Cockpit unavailable" message={error} />;

  const latestProposalRun = runs.find((run) => run.run_type === "proposal" || run.summary?.proposal_id);
  const latestRiskRun = runs.find((run) => run.run_type === "risk_check");
  const topCandidate = (lastScan?.candidates as Array<Record<string, unknown>> | undefined)?.[0];

  return (
    <div className="page-grid">
      <section className="hero-metrics">
        <article className="metric">
          <span>Equity</span>
          <strong>{money(account?.equity ?? account?.portfolio_value)}</strong>
        </article>
        <article className="metric">
          <span>Buying power</span>
          <strong>{money(account?.buying_power)}</strong>
        </article>
        <article className="metric">
          <span>Open positions</span>
          <strong>{positions.length}</strong>
        </article>
        <article className="metric">
          <span>Market</span>
          <strong>{clock?.is_open ? "Open" : "Closed"}</strong>
        </article>
      </section>

      <Card
        title="Agent actions"
        subtitle="Scan the universe and refresh cockpit state"
        action={
          <button className="button" onClick={() => void runScan()} disabled={scanning}>
            {scanning ? "Scanning…" : "Run scan"}
          </button>
        }
      >
        {topCandidate ? (
          <div className="stack">
            <div className="inline-badges">
              <StatusBadge label={String(topCandidate.symbol)} tone="ok" />
              <StatusBadge label={String(topCandidate.direction)} />
              <StatusBadge label={`Score ${topCandidate.score}`} />
            </div>
            <ul className="reason-list">
              {(topCandidate.reason_codes as string[] | undefined)?.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          </div>
        ) : (
          <p className="muted">No scan run yet in this session. Run a scan to rank candidates.</p>
        )}
      </Card>

      <Card title="Latest proposal & risk gate">
        <div className="two-col">
          <div>
            <h3>Proposal</h3>
            {latestProposalRun ? (
              <p>
                Run <code>{latestProposalRun.run_id}</code> · {latestProposalRun.status}
              </p>
            ) : (
              <p className="muted">No proposal runs recorded yet.</p>
            )}
          </div>
          <div>
            <h3>Risk gate</h3>
            {latestRiskRun ? (
              <p>
                {latestRiskRun.summary?.approved ? (
                  <StatusBadge label="Approved" tone="ok" />
                ) : (
                  <StatusBadge label="Rejected" tone="danger" />
                )}{" "}
                <code>{latestRiskRun.run_id}</code>
              </p>
            ) : (
              <p className="muted">No risk checks yet.</p>
            )}
          </div>
        </div>
      </Card>

      <Card title="Active positions" subtitle={`${positions.length} open`}>
        {positions.length === 0 ? (
          <p className="muted">No open positions.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Qty</th>
                  <th>Market value</th>
                  <th>Unrealized P&L</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((position) => (
                  <tr key={position.symbol}>
                    <td>{position.symbol}</td>
                    <td>{position.qty}</td>
                    <td>{money(position.market_value)}</td>
                    <td className={Number(position.unrealized_pl) >= 0 ? "positive" : "negative"}>
                      {money(position.unrealized_pl)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Card title="Orders & monitor" subtitle={`${orders.length} recent orders`}>
        <div className="two-col">
          <div>
            <h3>Orders</h3>
            {orders.slice(0, 5).map((order) => (
              <div key={order.id ?? order.client_order_id} className="list-row">
                <span>{order.symbol}</span>
                <StatusBadge
                  label={order.status ?? "unknown"}
                  tone={order.status === "filled" ? "ok" : "neutral"}
                />
              </div>
            ))}
          </div>
          <div>
            <h3>Monitor decisions</h3>
            {(monitor?.decisions ?? []).slice(0, 5).map((decision, index) => (
              <div key={`${decision.symbol}-${index}`} className="list-row">
                <span>{String(decision.symbol)}</span>
                <StatusBadge label={String(decision.action)} tone="warn" />
              </div>
            ))}
            {(monitor?.decisions ?? []).length === 0 ? (
              <p className="muted">No monitor decisions yet.</p>
            ) : null}
          </div>
        </div>
      </Card>

      <Card title="Recent audit runs">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Run</th>
                <th>Type</th>
                <th>Status</th>
                <th>Started</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr key={run.run_id}>
                  <td>
                    <code>{run.run_id}</code>
                  </td>
                  <td>{run.run_type}</td>
                  <td>{run.status}</td>
                  <td>{new Date(run.started_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
