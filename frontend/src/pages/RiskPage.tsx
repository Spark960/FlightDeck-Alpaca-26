import { useEffect, useState } from "react";

import { api, type AuditRunDetail } from "../api/client";
import { Card } from "../components/Card";
import { EmptyState, ErrorState, LoadingState } from "../components/StateViews";
import { StatusBadge } from "../components/StatusBadge";

export function RiskPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [checks, setChecks] = useState<Array<Record<string, unknown>>>([]);

  useEffect(() => {
    void (async () => {
      setLoading(true);
      try {
        const runs = await api.auditRuns(30);
        const riskRuns = runs.filter((run) => run.run_type === "risk_check").slice(0, 8);
        const details = await Promise.all(riskRuns.map((run) => api.auditRun(run.run_id)));
        const flattened = details.flatMap((detail: AuditRunDetail) =>
          (detail.risk_checks ?? []).map((check) => ({
            run_id: detail.run_id,
            started_at: detail.started_at,
            ...check,
          })),
        );
        setChecks(flattened);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load risk checks");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <LoadingState title="Risk console" />;
  if (error) return <ErrorState title="Risk console unavailable" message={error} />;
  if (checks.length === 0) {
    return <EmptyState title="No risk checks yet" message="Run a proposal through the risk gate to populate this view." />;
  }

  return (
    <div className="page-grid">
      <Card title="Recent risk gate decisions" subtitle="Deterministic checks before any order reaches execution">
        <div className="stack">
          {checks.map((check, index) => {
            const payload = (check.payload as Record<string, unknown>) ?? {};
            const approved = Boolean(check.approved);
            const blocking = (payload.blocking_reasons as string[] | undefined) ?? [];
            const warnings = (payload.warnings as string[] | undefined) ?? [];
            return (
              <article key={`${check.run_id}-${index}`} className="risk-item">
                <div className="list-row">
                  <div>
                    <strong>{String(check.run_id)}</strong>
                    <p className="muted">{new Date(String(check.started_at)).toLocaleString()}</p>
                  </div>
                  <StatusBadge label={approved ? "Approved" : "Rejected"} tone={approved ? "ok" : "danger"} />
                </div>
                {blocking.length > 0 ? (
                  <div>
                    <h4>Blocking reasons</h4>
                    <ul className="reason-list">
                      {blocking.map((reason) => (
                        <li key={reason}>{reason}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {warnings.length > 0 ? (
                  <div>
                    <h4>Warnings</h4>
                    <ul className="reason-list">
                      {warnings.map((warning) => (
                        <li key={warning}>{warning}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </article>
            );
          })}
        </div>
      </Card>
    </div>
  );
}
