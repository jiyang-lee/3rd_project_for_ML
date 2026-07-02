import { STATE_COLORS, type StateCard } from '../types'

interface Props {
  cards: Record<string, StateCard>
  substationIds: string[]
  selected: string | null
  onSelect: (id: string) => void
}

export default function SubstationGrid({ cards, substationIds, selected, onSelect }: Props) {
  return (
    <div className="grid">
      {substationIds.map((sid) => {
        const card = cards[sid]
        const state = card?.primary_state ?? 'unknown'
        const color = STATE_COLORS[state] ?? '#64748b'
        const preEvent = card?.pre_event_detected === 'true'
        return (
          <div
            key={sid}
            className={`tile ${selected === sid ? 'selected' : ''}`}
            onClick={() => onSelect(sid)}
          >
            {preEvent && <span className="pulse" title="pre-event 조기경보" />}
            <div className="sid">{sid}</div>
            <div className="state">
              <span className="dot" style={{ background: color }} />
              {state}
            </div>
            <div className="meta">
              {card
                ? `risk ${card.risk_probability != null ? card.risk_probability.toFixed(2) : '-'} · ${card.priority_tier}`
                : '카드 없음'}
            </div>
          </div>
        )
      })}
      {substationIds.length === 0 && <div className="empty">등록된 기계실이 없습니다 — 리플레이를 시작하세요</div>}
    </div>
  )
}
