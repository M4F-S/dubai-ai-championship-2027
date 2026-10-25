export type AgentType = 'taryaq' | 'qala' | 'nibras';

export interface Scenario {
  id: string;
  agent: AgentType;
  title_en: string;
  title_ar: string;
  prompt: string;
  expected: string;
  override_code: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'agent';
  content: string;
  toolCalls?: ToolCall[];
  piiRedactedBytes?: number;
  isBlocked?: boolean;
  alertCode?: string;
  signature?: string;
}

export interface ToolCall {
  name: string;
  args: Record<string, any>;
  result?: any;
  executionTimeMs?: number;
  isBlocked?: boolean;
}

export interface AuditRecord {
  timestamp_utc: number;
  reporting_tz: string;
  agent: string;
  action: string;
  state?: string;
  status?: string;
  prev_sha256?: string;
  sha256_signature: string;
  reason?: string;
  primary_drug?: string;
  concurrent_drug?: string;
  patient_egfr?: number;
  verdict?: string;
  alert_code?: string;
  override_token?: string;
}

export interface SystemHealth {
  c99_library_loaded: boolean;
  library_path: string;
  symbols: Record<string, boolean>;
  target_hardware: string;
  active_model: string;
  mode: string;
}
