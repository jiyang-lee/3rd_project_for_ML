import { AlertTriangle } from 'lucide-react'
import type { StateCard } from '../types'
import { TIER_LABEL } from '../types'

type Props = {
  readonly cards: readonly StateCard[]
  readonly selectedId: number | null
  readonly onSelect: (cardId: number) => void
}

export default function PriorityBoard({ cards, selectedId, onSelect }: Props) {
  if (cards.length === 0) {
    return <div className="empty">아직 생성된 우선순위 카드가 없습니다.</div>
  }

  return (
    <div className="priority-list">
      {cards.map((card) => (
        <button
          key={card.card_id}
          className={selectedId === card.card_id ? `priority-card ${card.priority_tier} selected` : `priority-card ${card.priority_tier}`}
          onClick={() => onSelect(card.card_id)}
        >
          <span className="tier-chip">{TIER_LABEL[card.priority_tier]}</span>
          <span className="card-title">{card.substation_id}</span>
          {card.review_flag && <AlertTriangle size={15} className="review-icon" aria-label="검토 필요" />}
          <span className="card-score">{card.priority_score?.toFixed(1) ?? '-'}</span>
          <span className="card-meta">{card.fault_group}</span>
          <span className="score-track">
            <span style={{ width: `${Math.min(100, Math.max(0, card.priority_score ?? 0))}%` }} />
          </span>
        </button>
      ))}
    </div>
  )
}
