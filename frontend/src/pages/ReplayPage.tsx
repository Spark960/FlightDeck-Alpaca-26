import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api, type AuditRun, type AuditRunDetail } from "../api/client";
import { Card } from "../components/Card";
import { EmptyState, ErrorState, LoadingState } from "../components/StateViews";

export function ReplayPage() {
  const [runs, setRuns] = useState<AuditRun[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<AuditRunDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      setLoading(true);
      try {
        const data = await api.auditRuns(40);
        setRuns(data);
        if (data[0]) setSelectedId(data[0].run_id);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load runs");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    void (async () => {
      setDetailLoading(true);
      try {
        const data = await api.auditRun(selectedId);
        setDetail(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load run detail");
      } finally {
        setDetailLoading(false);
      }
    })();
  }, [selectedId]);

  if (loading) return <LoadingState title="Replay" message="Loading audit runs…" />;
  if (error) return <ErrorState title="Replay unavailable" message={error} />;
  if (runs.length === 0) {
    return <EmptyState title="No runs yet" message="Trigger a scan or trade flow to populate the audit trail." />;
  }

  return (
    <div className="replay-layout">
      <Card title="Audit runs" subtitle="Select a run to inspect the flight recorder">
        <div className="run-list">
          {runs.map((run) => (
            <button
              key={run.run_id}
              className={`run-list__item ${selectedId === run.run_id ? "run-list__item--active" : ""}`}
              onClick={() => setSelectedId(run.run_id)}
            >
              <strong>{run.run_type}</strong>
              <span>{run.run_id}</span>
              <small>{new Date(run.started_at).toLocaleString()}</small>
            </button>
          ))}
        </div>
      </Card>

      <Card title="Run detail" subtitle={selectedId ?? undefined}>
        {detailLoading || !detail ? (
          <LoadingState title="Run detail" />
        ) : (
          <div className="stack">
            <div className="inline-badges">
              <span className="badge badge--neutral">{detail.status}</span>
              <span className="badge badge--neutral">{detail.run_type}</span>
            </div>

            <Section title="Summary" data={detail.summary} />
            <Section title="Market snapshots" data={detail.market_snapshots} />
            <Section title="Trade proposals" data={detail.trade_proposals} />
            <Section title="Risk checks" data={detail.risk_checks} />
            <Section title="Orders" data={detail.orders} />
            <Section title="Position snapshots" data={detail.position_snapshots} />
            <Section title="Agent events" data={detail.agent_events} />

            <p className="muted">
              Deep-link: <Link to={`/replay?run=${detail.run_id}`}>{detail.run_id}</Link>
            </p>
          </div>
        )}
      </Card>
    </div>
  );
}

function Section({ title, data }: { title: string; data: unknown }) {
  const items = Array.isArray(data) ? data : [data];
  if (!items.length || (items.length === 1 && items[0] == null)) {
    return (
      <div>
        <h3>{title}</h3>
        <p className="muted">None</p>
      </div>
    );
  }
  return (
    <div>
      <h3>{title}</h3>
      <pre className="code-block">{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}
