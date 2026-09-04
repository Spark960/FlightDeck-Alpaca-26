import {
  AccountInfo,
  AuditRunDetail,
  AuditRunItem,
  CliCommandResponse,
  CliRunResponse,
  CliStatusResponse,
  ExecuteTradeResponse,
  HealthResponse,
  MarketClock,
  MonitorResponse,
  Order,
  Position,
  ProposalReviewResponse,
  PublicSettings,
  RiskCheckResponse,
  ScanResponse,
  TradeProposal,
} from "../types/api";

const BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
  const headers = new Headers(options.headers || {});
  
  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }
  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = `Request failed: ${response.status} ${response.statusText}`;
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorJson.message || JSON.stringify(errorJson);
    } catch {
      // not a json response
    }
    throw new Error(errorDetail);
  }

  return response.json() as Promise<T>;
}

export const api = {
  // System & Health
  getHealth: () => request<HealthResponse>("/health"),
  getSettings: () => request<PublicSettings>("/api/settings"),

  // Account & Clock
  getAccount: () => request<AccountInfo>("/api/account"),
  getClock: () => request<MarketClock>("/api/clock"),
  getPositions: () => request<Position[]>("/api/positions"),
  getOrders: () => request<Order[]>("/api/orders"),

  // Scanner & Candidates
  scanMarket: (symbols?: string[], limit: number = 5) =>
    request<ScanResponse>("/api/scan", {
      method: "POST",
      body: JSON.stringify({ symbols, limit }),
    }),

  // Market Snapshot & Option Chain
  getMarketSnapshot: (symbols: string[]) =>
    request<Record<string, any>>(`/api/market/snapshot?symbols=${encodeURIComponent(symbols.join(","))}`),
  getOptionContracts: (symbol: string) =>
    request<Record<string, any>>(`/api/options/contracts/${symbol.toUpperCase()}`),
  getOptionChain: (symbol: string) =>
    request<Record<string, any>>(`/api/options/chain/${symbol.toUpperCase()}`),

  // Trade Proposals
  createProposal: (symbol: string, direction: "bullish" | "bearish" = "bullish", max_debit: number = 1500) =>
    request<TradeProposal>("/api/proposals", {
      method: "POST",
      body: JSON.stringify({ symbol: symbol.toUpperCase(), direction, max_debit }),
    }),
  getProposal: (proposalId: string) =>
    request<TradeProposal>(`/api/proposals/${proposalId}`),
  reviewProposal: (params: { proposal?: any; proposal_id?: string; market_candidate?: any }) =>
    request<ProposalReviewResponse>("/api/proposals/review", {
      method: "POST",
      body: JSON.stringify(params),
    }),

  // Risk Gates
  checkRisk: (params: { proposal?: any; proposal_id?: string }) =>
    request<RiskCheckResponse>("/api/risk/check", {
      method: "POST",
      body: JSON.stringify(params),
    }),

  // Trade Execution
  executeTrade: (proposalId: string, dryRun: boolean = true) =>
    request<ExecuteTradeResponse>(`/api/trades/execute/${proposalId}?dry_run=${dryRun}`, {
      method: "POST",
    }),
  syncOrders: () =>
    request<{ run_id: string; synced: Order[] }>("/api/trades/sync", {
      method: "POST",
    }),
  getOrderStatus: (orderId: string, refresh: boolean = false) =>
    request<{ order_id: string; stored: any; sync_result: any }>(
      `/api/trades/orders/${orderId}/status?refresh=${refresh}`
    ),

  // Autonomous Position Monitor
  runMonitor: (params: {
    sync_orders?: boolean;
    cli_proof?: boolean;
    execute_closes?: boolean;
    dry_run?: boolean;
  } = {}) => {
    const query = new URLSearchParams();
    if (params.sync_orders !== undefined) query.set("sync_orders", String(params.sync_orders));
    if (params.cli_proof !== undefined) query.set("cli_proof", String(params.cli_proof));
    if (params.execute_closes !== undefined) query.set("execute_closes", String(params.execute_closes));
    if (params.dry_run !== undefined) query.set("dry_run", String(params.dry_run));
    return request<MonitorResponse>(`/api/monitor/run?${query.toString()}`, {
      method: "POST",
    });
  },
  getLatestMonitorEvents: (limit: number = 20) =>
    request<{ decisions: any[]; alerts: any[]; actions: any[] }>(`/api/monitor/latest?limit=${limit}`),

  // Decision Replay & Audit
  listRuns: (limit: number = 50) =>
    request<AuditRunItem[]>(`/api/audit/runs?limit=${limit}`),
  getRunDetail: (runId: string) =>
    request<AuditRunDetail>(`/api/audit/runs/${runId}`),

  // Alpaca CLI Integration Proof
  getCliStatus: () => request<CliStatusResponse>("/api/integrations/cli/status"),
  getCliLatest: (limit: number = 20) =>
    request<any[]>(`/api/integrations/cli/latest?limit=${limit}`),
  runCliProof: () =>
    request<CliRunResponse>("/api/integrations/cli/run", {
      method: "POST",
    }),
  runCliCommand: (args: string[]) =>
    request<CliCommandResponse>("/api/integrations/cli/command", {
      method: "POST",
      body: JSON.stringify({ args }),
    }),
};
