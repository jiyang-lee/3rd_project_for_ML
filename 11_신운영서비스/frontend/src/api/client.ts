import type {
  ActionIntent,
  ActionResponse,
  CostDaily,
  RagChatResponse,
  RagChunk,
  ReplayScenariosResponse,
  ReplaySeekResponse,
  ReplayStatus,
  StateCard,
  Ticket
} from '../types'

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init)
  if (!response.ok) {
    throw new Error(`${url}: ${response.status}`)
  }
  return response.json()
}

export const api = {
  topCards: (n = 5) => fetchJson<readonly StateCard[]>(`/cards/top?n=${n}`),
  card: (cardId: number) => fetchJson<StateCard>(`/cards/${cardId}`),
  action: (cardId: number, intent: ActionIntent) =>
    fetchJson<ActionResponse>(`/cards/${cardId}/actions/${intent}`, { method: 'POST' }),
  tickets: () => fetchJson<readonly Ticket[]>('/tickets'),
  costs: () => fetchJson<CostDaily>('/llm/costs/daily'),
  replay: () => fetchJson<ReplayStatus>('/replay/status'),
  replayScenarios: () => fetchJson<ReplayScenariosResponse>('/replay/scenarios'),
  replayStart: () => fetchJson<{ readonly ok: boolean }>('/replay/start', { method: 'POST' }),
  replayStop: () => fetchJson<{ readonly ok: boolean }>('/replay/stop', { method: 'POST' }),
  replayTick: () => fetchJson<ReplaySeekResponse>('/replay/tick', { method: 'POST' }),
  replaySeek: (virtualTime: string) =>
    fetchJson<ReplaySeekResponse>('/replay/seek', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ virtual_time: virtualTime })
    }),
  patchTicket: (ticketId: number, status: string) =>
    fetchJson<Ticket>(`/tickets/${ticketId}?status=${encodeURIComponent(status)}`, { method: 'PATCH' }),
  ragSearch: (query: string) => fetchJson<readonly RagChunk[]>(`/rag/search?q=${encodeURIComponent(query)}`),
  ragChat: (question: string, limit = 5, context?: string) =>
    fetchJson<RagChatResponse>('/rag/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, context, limit })
    })
} as const
