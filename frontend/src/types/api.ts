export interface HealthResponse {
  status: string;
  app: string;
  paper_mode: boolean;
  demo_mode: boolean;
}

export interface PublicSettings {
  app: string;
  environment: string;
  paper_mode: boolean;
  demo_mode: boolean;
  alpaca_credentials_configured: boolean;
  alpaca_trading_base_url: string;
  alpaca_data_base_url: string;
  agent_credentials_configured: boolean;
  agent_base_url: string;
  agent_model: string;
  alpaca_cli_binary: string;
  scheduler_enabled: boolean;
  scheduler_interval_minutes: number;
}

export interface AccountInfo {
  account_number: string;
  status: string;
  currency: string;
  buying_power: number;
  cash: number;
  portfolio_value: number;
  equity: number;
  last_equity: number;
  daytrade_count?: number;
  initial_margin?: number;
  maintenance_margin?: number;
  sma?: number;
  pattern_day_trader?: boolean;
  trading_blocked?: boolean;
  transfers_blocked?: boolean;
  account_blocked?: boolean;
  created_at?: string;
  demo?: boolean;
}

export interface MarketClock {
  timestamp: string;
  is_open: boolean;
  next_open: string;
  next_close: string;
}

export interface Position {
  asset_id: string;
  symbol: string;
  exchange?: string;
  asset_class?: string;
  avg_entry_price: number;
  qty: number;
  side: "long" | "short";
  market_value: number;
  cost_basis: number;
  unrealized_pl: number;
  unrealized_plpc: number;
  unrealized_intraday_pl?: number;
  unrealized_intraday_plpc?: number;
  current_price: number;
  lastday_price?: number;
  change_today?: number;
  // Option specific fields when present
  expiration_date?: string;
  strike_price?: number;
  option_type?: "call" | "put";
}

export interface Order {
  id: string;
  client_order_id: string;
  created_at: string;
  updated_at?: string;
  submitted_at?: string;
  filled_at?: string;
  expired_at?: string;
  canceled_at?: string;
  asset_id?: string;
  symbol: string;
  asset_class?: string;
  qty: number;
  filled_qty?: number;
  filled_avg_price?: number;
  order_class?: string;
  order_type: string;
  type?: string;
  side: "buy" | "sell";
  time_in_force: string;
  limit_price?: number;
  stop_price?: number;
  status: string;
  legs?: Order[];
}

export interface MarketCandidate {
  symbol: string;
  score: number;
  direction: "bullish" | "bearish" | "none";
  price: number;
  return_1d: number;
  return_5d: number;
  intraday_return: number;
  gap_pct: number;
  volume_ratio: number;
  reasons: string[];
  rejection_reason?: string;
  quote_age_seconds: number;
}

export interface ScanResponse {
  run_id: string;
  universe: string[];
  candidates: MarketCandidate[];
  candidate_count: number;
}

export interface OptionLeg {
  symbol: string;
  side: "buy" | "sell";
  type: "call" | "put";
  strike: number;
  expiration: string;
  ratio_qty: number;
  bid: number;
  ask: number;
  mid: number;
  delta?: number;
  gamma?: number;
  theta?: number;
  vega?: number;
  implied_volatility?: number;
}

export interface TradeProposal {
  run_id?: string;
  proposal_id?: string;
  symbol?: string;
  underlying_symbol: string;
  strategy_type: string;
  direction: "bullish" | "bearish";
  accepted: boolean;
  rejection_reason?: string;
  rejection_reasons?: string[];
  legs: OptionLeg[];
  net_debit: number;
  max_loss: number;
  max_profit?: number;
  break_even?: number;
  expiration: string;
  rationale?: string;
  created_at?: string;
}

export interface AnalystThesis {
  symbol: string;
  market_regime: string;
  strategy_type: string;
  thesis: string;
  evidence: string[];
  invalidation_condition: string;
  expected_holding_period: string;
  max_loss: number;
  confidence: number;
}

export interface CriticReview {
  passed: boolean;
  verdict: "pass" | "revise" | "reject";
  issues: string[];
  critique: string;
}

export interface ProposalReviewResponse {
  run_id: string;
  proposal_id?: string;
  source: string;
  analyst: AnalystThesis;
  critic: CriticReview;
}

export interface RiskCheckResponse {
  run_id: string;
  proposal_id?: string;
  approved: boolean;
  blocking_reasons: string[];
  warnings: string[];
  computed_risk: {
    max_loss: number;
    risk_pct_of_equity: number;
    premium_deployed_pct: number;
    contracts: number;
  };
  checks_evaluated: Record<string, boolean>;
  timestamp: string;
}

export interface ExecuteTradeResponse {
  run_id: string;
  proposal_id: string;
  dry_run: boolean;
  risk_approved: boolean;
  order_payload?: Record<string, any>;
  order_id?: string;
  alpaca_response?: Record<string, any>;
  blocking_reasons?: string[];
}

export interface MonitorDecision {
  symbol: string;
  action: string;
  reason: string;
  priority: number;
  should_close: boolean;
  metrics: {
    unrealized_plpc?: number;
    unrealized_pl?: number;
    cost_basis?: number;
    current_value?: number;
    dte?: number;
    holding_days?: number;
    [key: string]: any;
  };
}

export interface MonitorResponse {
  run_id: string;
  timestamp: string;
  account: Record<string, any>;
  position_count: number;
  open_order_count: number;
  decisions: MonitorDecision[];
  alerts: Array<{
    level: "warning" | "critical" | "info";
    code: string;
    message: string;
    symbol?: string;
  }>;
  summary: {
    held: number;
    take_profit: number;
    stop_loss: number;
    time_stop: number;
    expiration_risk: number;
    unpaired: number;
  };
  synced_orders: Array<Record<string, any>>;
  executed_closes: Array<Record<string, any>>;
  cli_proof?: Record<string, any> | null;
}

export interface AuditRunItem {
  run_id: string;
  run_type: string;
  status: string;
  started_at: string;
  completed_at?: string;
  summary: Record<string, any>;
}

export interface AuditRunDetail extends AuditRunItem {
  market_snapshot?: Record<string, any>;
  option_chains?: Array<Record<string, any>>;
  trade_proposal?: Record<string, any>;
  risk_check?: Record<string, any>;
  order?: Record<string, any>;
  position_snapshot?: Record<string, any>;
  agent_events: Array<{
    id: number;
    run_id: string;
    event_type: string;
    payload: Record<string, any>;
    created_at: string;
  }>;
}

export interface CliStatusResponse {
  installed: boolean;
  binary: string;
  version?: string;
  error?: string;
}

export interface CliCommandResponse {
  result: {
    command: string[];
    exit_code: number;
    stdout: string;
    stderr: string;
    parsed_json?: any;
    duration_ms: number;
  };
}

export interface CliRunResponse {
  run_id: string;
  summary: {
    commands_executed: number;
    commands_succeeded: number;
    commands_failed: number;
    duration_ms: number;
  };
  results: Array<{
    command: string[];
    exit_code: number;
    stdout: string;
    stderr: string;
    parsed_json?: any;
    duration_ms: number;
  }>;
}
