export interface User {
  id: string
  email: string
  role: string
}

export interface Application {
  id: string
  name: string
  description: string | null
  created_by: string
  created_at: string
  updated_at: string
}

export interface PromptTemplate {
  id: string
  application_id: string
  name: string
  description: string | null
  created_at: string
  updated_at: string
  versions?: PromptVersion[]
}

export interface PromptVersion {
  id: string
  template_id: string
  version_number: number
  content: string
  variables: Record<string, string> | null
  model_config_json: Record<string, unknown> | null
  tag: string | null
  commit_message: string | null
  created_by: string | null
  created_at: string
  [key: string]: unknown
}

export interface Experiment {
  id: string
  application_id: string
  name: string
  status: 'draft' | 'running' | 'completed' | 'cancelled'
  started_at: string | null
  ended_at: string | null
  created_by: string
  created_at: string
  variants: ExperimentVariant[]
  app_id?: string
  variants_count?: number
  [key: string]: unknown
}

export interface ExperimentVariant {
  id: string
  prompt_version_id: string
  traffic_pct: number
  label: string
  name?: string
  conversion_rate?: number
  avg_latency_ms?: number
}

export interface ExperimentResult {
  id: string
  variant_id: string
  request_count: number
  metrics: Record<string, number> | null
  p_value: number | null
  is_winner: boolean | null
  updated_at: string
}

export interface ExperimentResultSummary {
  winner?: { id: string; name: string } | null
  total_requests?: number
  p_value?: number | null
  variants?: Array<{ id?: string; name: string; conversion_rate?: number; avg_latency_ms?: number; [key: string]: unknown }>
  convergence?: Array<Record<string, unknown>>
  results?: ExperimentResult[]
}

export interface EvalDataset {
  id: string
  application_id: string
  name: string
  dataset_type: string
  description: string | null
  created_at: string
  item_count: number
  [key: string]: unknown
}

export interface EvalRun {
  id: string
  prompt_version_id: string
  dataset_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  trigger: string
  aggregate_scores: Record<string, number> | null
  created_at: string
  completed_at: string | null
  overall_score?: number | null
}

export interface EvalResult {
  id: string
  eval_run_id: string
  dataset_item_id: string
  llm_response: string | null
  scores: Record<string, number> | null
  latency_ms: number | null
  token_usage: { input: number; output: number } | null
  cost_usd: number | null
  created_at: string
  input?: string
  expected?: string
  actual?: string
  score?: number
  metrics?: Record<string, number>
  [key: string]: unknown
}

export interface HumanEvalCampaign {
  id: string
  eval_run_id: string
  name: string
  dimensions: Record<string, unknown>
  status: string
  created_at: string
  total_assignments: number
  completed_assignments: number
  items?: Array<{ id: string; input?: string; output?: string; output_a?: string; output_b?: string; [key: string]: unknown }>
  total_items?: number
  completed_items?: number
  description?: string
  reviewers_count?: number
  score_distribution?: Array<{ score: string | number; count: number }>
  reviewers?: Array<{ email: string; completed: number; total: number }>
  [key: string]: unknown
}

export interface CostAnalytics {
  total_cost_usd: number
  total_requests: number
  total_input_tokens: number
  total_output_tokens: number
  cache_hit_rate: number
  breakdown: Array<{ period: string; cost: number; requests: number }>
  total_tokens?: number
  input_tokens?: number
  output_tokens?: number
  token_usage_over_time?: Array<Record<string, unknown>>
  tokens_by_model?: Array<Record<string, unknown>>
  tokens_by_app?: Array<Record<string, unknown>>
  [key: string]: unknown
}

export interface BudgetAlert {
  id: string
  application_id: string
  budget_usd: number
  period: string
  alert_pct: number[]
  is_active: boolean
  last_triggered_pct: number | null
  created_at: string
  name?: string
  threshold?: number
  current_spend?: number
  status?: string
  notification_channels?: string[]
  [key: string]: unknown
}

export interface Deployment {
  id: string
  application_id: string
  prompt_version_id: string
  status: string
  canary_pct: number
  eval_run_id: string | null
  previous_version_id: string | null
  deployed_by: string
  created_at: string
  updated_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface PromptDiffDetailed {
  v1: number
  v2: number
  v1_content: string
  v2_content: string
  v1_tag: string | null
  v2_tag: string | null
  v1_commit_message: string | null
  v2_commit_message: string | null
  v1_created_at: string | null
  v2_created_at: string | null
  v1_variables: string[]
  v2_variables: string[]
  variables_added: string[]
  variables_removed: string[]
  lines_added: number
  lines_removed: number
  lines_changed: number
}

export interface RegressionCheck {
  has_regression: boolean
  current_version: number
  previous_version: number
  current_scores: Record<string, number>
  previous_scores: Record<string, number>
  regressions: Array<{ metric: string; current: number; previous: number; delta: number; pct_change: number }>
  improvements: Array<{ metric: string; current: number; previous: number; delta: number; pct_change: number }>
  threshold_pct: number
}
