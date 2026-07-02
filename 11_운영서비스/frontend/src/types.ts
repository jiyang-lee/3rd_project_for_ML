export interface Substation {
  substation_id: string
  manufacturer: string
  raw_id: number
  system_capability_group: string | null
  common10_ready: boolean | null
  active: boolean
  primary_state: string | null
  priority_tier: string | null
  risk_probability: number | null
  pre_event_detected: string | null
  review_flag: boolean | null
  last_window_end: string | null
  last_card_id: number | null
}

export interface StateCard {
  card_id: number
  sample_id: string
  substation_id: string
  window_start: string
  window_end: string
  created_at?: string
  data_scope: string
  primary_state: string
  secondary_tags: string
  fault_detected: boolean
  task_detected: boolean
  activity_detected: boolean
  fault_probability: number | null
  task_probability: number | null
  activity_probability: number | null
  pre_event_detected: string
  risk_probability: number | null
  fault_group: string
  leadtime_label: string
  leadtime_urgency: number | null
  group_weight: number | null
  priority_score: number | null
  priority_tier: string
  review_flag: boolean
  review_reasons: string
  why_reason: string
  coverage_rate: number | null
  validation_level: string
  features: Record<string, number | null> | null
}

export interface DispatchOrder {
  order_id: number
  card_id: number
  substation_id: string
  created_at: string
  virtual_time: string | null
  priority_tier: string | null
  priority_score: number | null
  title: string
  body_markdown: string
  recommended_action: string
  generated_by: string
  status: string
}

export interface AgentRun {
  run_id: number
  started_at: string
  trigger_card_ids: number[]
  status: string
  node_trace: Record<string, unknown> | null
  error: string | null
}

export interface ReplayStatus {
  virtual_time: string | null
  speed_factor: number | null
  running: boolean
  updated_at?: string
}

export interface WsEvent {
  type: 'clock' | 'state_card' | 'dispatch_order' | 'agent_run'
  payload: any
}

export const STATE_COLORS: Record<string, string> = {
  normal: '#22c55e',
  activity: '#3b82f6',
  task: '#f59e0b',
  fault: '#ef4444',
  review_required: '#a855f7',
}

export const TIER_COLORS: Record<string, string> = {
  high: '#ef4444',
  medium: '#f59e0b',
  low: '#3b82f6',
  monitor: '#64748b',
}
