import { Activity, Clock3, Database, FileText, ReceiptText, Search } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from './api/client'
import { useWebSocket } from './api/ws'
import CardDetail from './components/CardDetail'
import CostDashboard from './components/CostDashboard'
import PriorityBoard from './components/PriorityBoard'
import RagSearch from './components/RagSearch'
import ReplayClock from './components/ReplayClock'
import TicketBoard from './components/TicketBoard'
import type { CostDaily, ReplayStatus, StateCard, Ticket, WsEvent } from './types'

type TabId = 'priority' | 'tickets' | 'costs' | 'rag'

const tabs: readonly { readonly id: TabId; readonly label: string; readonly icon: typeof Activity }[] = [
  { id: 'priority', label: '우선순위', icon: Activity },
  { id: 'tickets', label: '티켓', icon: ReceiptText },
  { id: 'costs', label: '비용', icon: Clock3 },
  { id: 'rag', label: 'RAG', icon: Search }
] as const

export default function App() {
  const [cards, setCards] = useState<readonly StateCard[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [tickets, setTickets] = useState<readonly Ticket[]>([])
  const [costs, setCosts] = useState<CostDaily | null>(null)
  const [replay, setReplay] = useState<ReplayStatus | null>(null)
  const [tab, setTab] = useState<TabId>('priority')
  const [statusText, setStatusText] = useState('동기화 전')

  const selected = useMemo(
    () => cards.find((card) => card.card_id === selectedId) ?? cards[0],
    [cards, selectedId]
  )

  const refresh = useCallback(() => {
    setStatusText('동기화 중')
    void Promise.allSettled([api.topCards(10), api.tickets(), api.costs(), api.replay()]).then(
      ([cardsResult, ticketsResult, costsResult, replayResult]) => {
        if (cardsResult.status === 'fulfilled') {
          setCards(cardsResult.value)
        }
        if (ticketsResult.status === 'fulfilled') {
          setTickets(ticketsResult.value)
        }
        if (costsResult.status === 'fulfilled') {
          setCosts(costsResult.value)
        }
        if (replayResult.status === 'fulfilled') {
          setReplay(replayResult.value)
        }
        const failed = [cardsResult, ticketsResult, costsResult, replayResult].filter((result) => result.status === 'rejected').length
        const now = new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })
        setStatusText(failed === 0 ? `동기화됨 ${now}` : `${failed}개 API 대기 · ${now}`)
      }
    )
  }, [])

  useEffect(() => {
    refresh()
    const timer = window.setInterval(refresh, 15000)
    return () => window.clearInterval(timer)
  }, [refresh])

  useWebSocket((event: WsEvent) => {
    if (event.type === 'state_card') {
      setStatusText('새 카드 수신')
      api.topCards(10).then(setCards).catch(() => undefined)
    }
    if (event.type === 'clock') {
      setStatusText('리플레이 시계 갱신')
      api.replay().then(setReplay).catch(() => undefined)
    }
    if (event.type === 'ticket') {
      setStatusText('새 티켓 수신')
      api.tickets().then(setTickets).catch(() => undefined)
    }
  })

  const urgentCount = cards.filter((card) => card.priority_tier === 'urgent' || card.priority_tier === 'high').length
  const activeTicketCount = tickets.filter((ticket) => ticket.status !== 'done').length

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">HeatGrid 신운영서비스</p>
          <h1>오늘 볼 운영 카드</h1>
        </div>
        <div className="topbar-metrics" aria-label="운영 현황">
          <div className="metric-inline">
            <Database size={16} />
            <span>{cards.length} cards</span>
          </div>
          <div className="metric-inline danger">
            <Activity size={16} />
            <span>{urgentCount} high+</span>
          </div>
          <div className="metric-inline">
            <ReceiptText size={16} />
            <span>{activeTicketCount} tickets</span>
          </div>
          <ReplayClock status={replay} onRefresh={refresh} />
        </div>
      </header>

      <section className="layout">
        <aside className="worklist" aria-label="우선순위 카드 목록">
          <PriorityBoard cards={cards} selectedId={selected?.card_id ?? null} onSelect={setSelectedId} />
        </aside>

        <section className="detail">
          <nav className="tabs" aria-label="운영 탭">
            {tabs.map((item) => {
              const Icon = item.icon
              return (
                <button key={item.id} className={tab === item.id ? 'tab active' : 'tab'} onClick={() => setTab(item.id)}>
                  <Icon size={16} />
                  <span>{item.label}</span>
                </button>
              )
            })}
          </nav>

          {tab === 'priority' && (
            <CardDetail
              card={selected}
              onActionComplete={refresh}
              onOpenRag={() => setTab('rag')}
              onOpenTickets={() => setTab('tickets')}
            />
          )}
          {tab === 'tickets' && <TicketBoard tickets={tickets} onTicketUpdated={refresh} />}
          {tab === 'costs' && <CostDashboard costs={costs} />}
          {tab === 'rag' && <RagSearch card={selected} />}
        </section>
      </section>

      <footer className="statusbar">
        <FileText size={14} />
        <span>{statusText}</span>
      </footer>
    </main>
  )
}
