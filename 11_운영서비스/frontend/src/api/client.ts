import type { AgentRun, DispatchOrder, ReplayStatus, StateCard, Substation } from '../types'

async function getJson<T>(url: string): Promise<T> {
  const resp = await fetch(url)
  if (!resp.ok) throw new Error(`${url}: ${resp.status}`)
  return resp.json()
}

export const api = {
  substations: () => getJson<Substation[]>('/api/substations'),
  latestCards: () => getJson<StateCard[]>('/api/state-cards/latest'),
  cardDetail: (cardId: number) => getJson<StateCard>(`/api/state-cards/${cardId}`),
  cardHistory: (substationId: string, limit = 100) =>
    getJson<StateCard[]>(`/api/substations/${substationId}/state-cards?limit=${limit}`),
  readings: (substationId: string, hours = 168, signals?: string) =>
    getJson<{ signals: string[]; rows: Record<string, any>[] }>(
      `/api/substations/${substationId}/readings?hours=${hours}${signals ? `&signals=${signals}` : ''}`,
    ),
  orders: (status?: string) =>
    getJson<DispatchOrder[]>(`/api/dispatch-orders${status ? `?status=${status}` : ''}`),
  patchOrder: async (orderId: number, status: string) => {
    const resp = await fetch(`/api/dispatch-orders/${orderId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    })
    if (!resp.ok) throw new Error(`patch order failed: ${resp.status}`)
    return resp.json()
  },
  agentRuns: () => getJson<AgentRun[]>('/api/agent-runs'),
  replayStatus: () => getJson<ReplayStatus>('/api/replay/status'),
}
