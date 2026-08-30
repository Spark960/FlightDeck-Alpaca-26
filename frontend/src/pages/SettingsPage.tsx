import { useEffect, useState } from "react";

import { api, type AppSettings } from "../api/client";
import { Card } from "../components/Card";
import { ErrorState, LoadingState } from "../components/StateViews";
import { StatusBadge } from "../components/StatusBadge";

export function SettingsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [cliStatus, setCliStatus] = useState<Record<string, unknown> | null>(null);
  const [cliRunning, setCliRunning] = useState(false);
  const [cliResult, setCliResult] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const [settingsData, cliData] = await Promise.all([api.settings(), api.cliStatus()]);
        setSettings(settingsData);
        setCliStatus(cliData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load settings");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const runCliProof = async () => {
    setCliRunning(true);
    try {
      const result = await api.cliRun();
      setCliResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "CLI proof failed");
    } finally {
      setCliRunning(false);
    }
  };

  if (loading) return <LoadingState title="Settings" />;
  if (error && !settings) return <ErrorState title="Settings unavailable" message={error} />;

  return (
    <div className="page-grid">
      <Card title="Environment">
        {settings ? (
          <div className="settings-grid">
            <Setting label="App" value={settings.app} />
            <Setting label="Environment" value={settings.environment} />
            <Setting label="Agent model" value={settings.agent_model} />
            <Setting
              label="Demo mode"
              value={settings.demo_mode ? "Enabled" : "Disabled"}
              badge={settings.demo_mode ? "warn" : "ok"}
            />
            <Setting
              label="Paper mode"
              value={settings.paper_mode ? "Enabled" : "Disabled"}
              badge="ok"
            />
            <Setting
              label="Alpaca credentials"
              value={settings.alpaca_credentials_configured ? "Configured" : "Missing"}
              badge={settings.alpaca_credentials_configured ? "ok" : "warn"}
            />
            <Setting
              label="Agent credentials"
              value={settings.agent_credentials_configured ? "Configured" : "Missing"}
              badge={settings.agent_credentials_configured ? "ok" : "warn"}
            />
          </div>
        ) : null}
      </Card>

      <Card
        title="Alpaca CLI integration"
        subtitle="Hackathon MCP/CLI proof path"
        action={
          <button className="button" onClick={() => void runCliProof()} disabled={cliRunning}>
            {cliRunning ? "Running…" : "Run CLI proof"}
          </button>
        }
      >
        {cliStatus ? (
          <div className="stack">
            <div className="inline-badges">
              <StatusBadge
                label={cliStatus.cli_available ? "CLI installed" : "CLI not on PATH"}
                tone={cliStatus.cli_available ? "ok" : "warn"}
              />
              <StatusBadge label={`Binary: ${String(cliStatus.binary)}`} />
            </div>
            <pre className="code-block">{JSON.stringify(cliStatus.default_commands, null, 2)}</pre>
          </div>
        ) : null}
        {cliResult ? <pre className="code-block">{JSON.stringify(cliResult, null, 2)}</pre> : null}
        {error ? <p className="error-text">{error}</p> : null}
      </Card>
    </div>
  );
}

function Setting({
  label,
  value,
  badge,
}: {
  label: string;
  value: string;
  badge?: "ok" | "warn" | "danger" | "neutral";
}) {
  return (
    <div className="setting-row">
      <span>{label}</span>
      <div className="inline-badges">
        {badge ? <StatusBadge label={value} tone={badge} /> : <strong>{value}</strong>}
      </div>
    </div>
  );
}
