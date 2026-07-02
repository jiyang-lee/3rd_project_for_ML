import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from './api/client'
import { useWebSocket } from './api/ws'
import AgentTrace from './components/AgentTrace'
import DispatchFeed from './components/DispatchFeed'
import PriorityBoard from './components/PriorityBoard'
import ReplayClock from './components/ReplayClock'
import StateCardPanel from './components/StateCardPanel'
import SubstationGrid from './components/SubstationGrid'
import { STATE_COLORS, type AgentRun, type DispatchOrder, type ReplayStatus, type StateCard, type WsEvent } from './types'

type Tab = 'priority' | 'dispatch' | 'agent'

export default function App() {
  const [replay, setReplay] = useState<ReplayStatus | null>(null)
  const [cards, setCards] = useState<Record<string, StateCard>>({})
  const [substationIds, setSubstationIds] = useState<string[]>([])
  const [orders, setOrders] = useState<DispatchOrder[]>([])
  const [runs, setRuns] = useState<AgentRun[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [tab, setTab] = useState<Tab>('priority')

  const refreshAll = useCallback(() => {
    api.replayStatus().then(setReplay).catch(() => {})
    api.substations()
      .then((subs) => setSubstationIds(subs.map((s) => s.substation_id)))
      .catch(() => {})
    api.latestCards()
      .then((list) => {
        const map: Record<string, StateCard> = {}
        for (const c of list) map[c.substation_id] = c
        setCards(map)
      })
      .catch(() => {})
    api.orders().then(setOrders).catch(() => {})
    api.agentRuns().then(setRuns).catch(() => {})
  }, [])

  useEffect(() => {
    refreshAll()
    const id = setInterval(refreshAll, 15000) // WS 유실 대비 폴링 백업
    return () => clearInterval(id)
  }, [refreshAll])

  useWebSocket((event: WsEvent) => {
    if (event.type === 'clock') {
      setReplay((prev) => ({ ...prev, ...event.payload }))
    } else if (event.type === 'state_card') {
      const card = event.payload as StateCard
      setCards((prev) => ({ ...prev, [card.substation_id]: card }))
      setSubstationIds((prev) => (prev.includes(card.substation_id) ? prev : [...prev, card.substation_id].sort()))
    } else if (event.type === 'dispatch_order') {
      setOrders((prev) => [event.payload as DispatchOrder, ...prev])
    } else if (event.type === 'agent_run') {
      setRuns((prev) => [event.payload as AgentRun, ...prev])
    }
  })

  const counters = useMemo(() => {
    const counts: Record<string, number> = {}
    for (const c of Object.values(cards)) counts[c.primary_state] = (counts[c.primary_state] ?? 0) + 1
    return counts
  }, [cards])

  return (
    <div className="app">
      <header className="header">
        <h1>HeatGrid 운영 대시보드</h1>
        <ReplayClock status={replay} />
        <div className="counters">
          {Object.entries(counters).map(([state, n]) => (
            <span className="counter" key={state}>
              <span className="dot" style={{ background: STATE_COLORS[state] ?? '#64748b' }} />
              {state} {n}
            </span>
          ))}
        </div>
      </header>
      <div className="main">
        <div className="left">
          <SubstationGrid cards={cards} substationIds={substationIds} selected={selected} onSelect={setSelected} />
        </div>
        <div className="right">
          <div className="tabs">
            <button className={tab === 'priority' ? 'active' : ''} onClick={() => setTab('priority')}>
              우선순위
            </button>
            <button className={tab === 'dispatch' ? 'active' : ''} onClick={() => setTab('dispatch')}>
              출동지시 ({orders.filter((o) => o.status === 'draft').length})
            </button>
            <button className={tab === 'agent' ? 'active' : ''} onClick={() => setTab('agent')}>
              에이전트
            </button>
          </div>
          <div className="tab-body">
            {tab === 'priority' && <PriorityBoard cards={cards} />}
            {tab === 'dispatch' && <DispatchFeed orders={orders} onChanged={refreshAll} />}
            {tab === 'agent' && <AgentTrace runs={runs} />}
          </div>
        </div>
      </div>
      {selected && <StateCardPanel substationId={selected} latestCard={cards[selected]} />}
    </div>
  )
}
