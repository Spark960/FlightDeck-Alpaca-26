const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: string };
      detail = body.detail ?? detail;
    } catch {
      // ignore parse errors
    }
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export type AppSettings = {
  app: string;
  environment: string;
  paper_mode: boolean;
  demo_mode: boolean;
  alpaca_credentials_configured: boolean;
  agent_credentials_configured: boolean;
  agent_model: string;
  alpaca_cli_binary: string;
};

export type AuditRun = {
  run_id: string;
  run_type: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  summary: Record<string, unknown>;
};

export type AuditRunDetail = AuditRun & {
  market_snapshots: Array<Record<string, unknown>>;
  option_chains: Array<Record<string, unknown>>;
  trade_proposals: Array<Record<string, unknown>>;
  risk_checks: Array<Record<string, unknown>>;
  orders: Array<Record<string, unknown>>;
  position_snapshots: Array<Record<string, unknown>>;
  agent_events: Array<Record<string, unknown>>;
};

export const api = {
  health: () => request<{ status: string; demo_mode: boolean }>("/health"),
  settings: () => request<AppSettings>("/api/settings"),
  account: () => request<Record<string, string>>("/api/account"),
  clock: () => request<Record<string, unknown>>("/api/clock"),
  positions: () => request<Array<Record<string, string>>>("/api/positions"),
  orders: () => request<Array<Record<string, string>>>("/api/orders"),
  scan: (limit = 5) =>
    request<Record<string, unknown>>("/api/scan", {
      method: "POST",
      body: JSON.stringify({ limit }),
    }),
  auditRuns: (limit = 50) => request<AuditRun[]>(`/api/audit/runs?limit=${limit}`),
  auditRun: (runId: string) => request<AuditRunDetail>(`/api/audit/runs/${runId}`),
  monitorLatest: () =>
    request<{
      decisions: Array<Record<string, unknown>>;
      alerts: Array<Record<string, unknown>>;
      actions: Array<Record<string, unknown>>;
    }>("/api/monitor/latest"),
  monitorRun: (params?: { sync_orders?: boolean; cli_proof?: boolean }) => {
    const query = new URLSearchParams();
    if (params?.sync_orders !== undefined) query.set("sync_orders", String(params.sync_orders));
    if (params?.cli_proof !== undefined) query.set("cli_proof", String(params.cli_proof));
    const suffix = query.toString() ? `?${query}` : "";
    return request<Record<string, unknown>>(`/api/monitor/run${suffix}`, { method: "POST" });
  },
  cliStatus: () => request<Record<string, unknown>>("/api/integrations/cli/status"),
  cliRun: () => request<Record<string, unknown>>("/api/integrations/cli/run", { method: "POST" }),
};
