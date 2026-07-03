export type PriorityTier = 'urgent' | 'high' | 'medium' | 'low' | 'monitor' | 'not_applicable'

export type ActionIntent = 'explain_priority' | 'report' | 'vendor_message' | 'resident_notice'

export type StateCard = {
  readonly card_id: number
  readonly sample_id: string
  readonly substation_id: string
  readonly window_start: string
  readonly window_end: string
  readonly data_scope: string
  readonly primary_state: string
  readonly secondary_tags: string
  readonly fault_probability: number | null
  readonly task_probability: number | null
  readonly activity_probability: number | null
  readonly pre_event_detected: string
  readonly risk_probability: number | null
  readonly fault_group: string
  readonly leadtime_label: string
  readonly priority_score: number | null
  readonly priority_tier: PriorityTier
  readonly review_flag: boolean
  readonly review_reasons: string
  readonly why_reason: string
  readonly coverage_rate: number | null
  readonly validation_level: string
  readonly features: Record<string, number | null> | null
}

export type ActionResponse = {
  readonly text: string
  readonly generated_by: string
  readonly cached: boolean
  readonly tokens: number
}

export type Ticket = {
  readonly ticket_id: number
  readonly card_id: number
  readonly intent: string
  readonly status: string
  readonly text: string
  readonly generated_by: string
  readonly created_at: string
}

export type ReplayStatus = {
  readonly virtual_time: string | null
  readonly speed_factor: number | null
  readonly running: boolean
  readonly updated_at?: string
}

export type ReplayTimeRange = {
  readonly start: string | null
  readonly end: string | null
  readonly count: number
}

export type ReplayScenario = {
  readonly scenario_id: string
  readonly label: string
  readonly virtual_time: string
  readonly substation_id: string
  readonly priority_tier: PriorityTier
  readonly fault_group: string
  readonly leadtime_label: string
  readonly priority_score: number | null
  readonly description: string
}

export type ReplayScenariosResponse = {
  readonly time_range: ReplayTimeRange
  readonly scenarios: readonly ReplayScenario[]
}

export type ReplaySeekResponse = {
  readonly ok: boolean
  readonly requested_time: string
  readonly virtual_time: string
  readonly card_ids: readonly number[]
}

export type CostDaily = {
  readonly prompt_tokens: number
  readonly completion_tokens: number
  readonly estimated_cost_usd: number
  readonly calls: number
  readonly cache_hits: number
}

export type RagChunk = {
  readonly chunk_id: number
  readonly title: string
  readonly breadcrumb: string | null
  readonly content: string
}

export type RagChatResponse = {
  readonly answer: string
  readonly generated_by: string
  readonly tokens: number
  readonly sources: readonly RagChunk[]
}

export type WsEvent = {
  readonly type: string
  readonly payload: unknown
}

export const TIER_LABEL: Record<PriorityTier, string> = {
  urgent: '긴급',
  high: '높음',
  medium: '중간',
  low: '낮음',
  monitor: '관찰',
  not_applicable: '해당 없음'
} as const
