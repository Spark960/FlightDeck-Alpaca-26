import { useEffect, useState } from "react";

import { api } from "../api/client";
import { Card } from "../components/Card";
import { ErrorState, LoadingState } from "../components/StateViews";
import { StatusBadge } from "../components/StatusBadge";

function money(value: string | number | undefined) {
  const amount = Number(value ?? 0);
  return amount.toLocaleString(undefined, { style: "currency", currency: "USD" });
}

export function PositionsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [positions, setPositions] = useState<Array<Record<string, string>>>([]);
  const [monitor, setMonitor] = useState<Awaited<ReturnType<typeof api.monitorLatest>> | null>(null);
  const [running, setRunning] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [positionData, monitorData] = await Promise.all([api.positions(), api.monitorLatest()]);
      setPositions(positionData);
      setMonitor(monitorData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load positions");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const runMonitor = async () => {
    setRunning(true);
    try {
      await api.monitorRun({ sync_orders: true, cli_proof: false });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Monitor run failed");
    } finally {
      setRunning(false);
    }
  };

  if (loading) return <LoadingState title="Positions" />;
  if (error) return <ErrorState title="Positions unavailable" message={error} />;

  return (
    <div className="page-grid">
      <Card
        title="Open positions"
        action={
          <button className="button" onClick={() => void runMonitor()} disabled={running}>
            {running ? "Running monitor…" : "Run monitor"}
          </button>
        }
      >
        {positions.length === 0 ? (
          <p className="muted">No open positions. Demo mode still shows sample data when enabled.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Qty</th>
                  <th>Cost basis</th>
                  <th>Market value</th>
                  <th>Unrealized P&L</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((position) => (
                  <tr key={position.symbol}>
                    <td>{position.symbol}</td>
                    <td>{position.qty}</td>
                    <td>{money(position.cost_basis)}</td>
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

      <Card title="Monitor decisions">
        {(monitor?.decisions ?? []).length === 0 ? (
          <p className="muted">No monitor decisions recorded.</p>
        ) : (
          <div className="stack">
            {(monitor?.decisions ?? []).map((decision, index) => (
              <div key={`${decision.symbol}-${index}`} className="list-row">
                <div>
                  <strong>{String(decision.symbol)}</strong>
                  <p className="muted">{String(decision.reason)}</p>
                </div>
                <StatusBadge label={String(decision.action)} tone="warn" />
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card title="Monitor alerts">
        {(monitor?.alerts ?? []).length === 0 ? (
          <p className="muted">No alerts.</p>
        ) : (
          <pre className="code-block">{JSON.stringify(monitor?.alerts, null, 2)}</pre>
        )}
      </Card>
    </div>
  );
}
