import { TIER_COLORS, type StateCard } from '../types'

export default function PriorityBoard({ cards }: { cards: Record<string, StateCard> }) {
  const ranked = Object.values(cards)
    .filter((c) => c.priority_tier === 'high' || c.priority_tier === 'medium' || c.priority_tier === 'low')
    .sort((a, b) => (b.priority_score ?? 0) - (a.priority_score ?? 0))
  if (ranked.length === 0) return <div className="empty">우선순위 대상 카드가 없습니다</div>
  return (
    <div>
      {ranked.map((c) => (
        <div className="priority-item" key={c.card_id}>
          <span className="tier" style={{ background: TIER_COLORS[c.priority_tier] ?? '#64748b' }}>
            {c.priority_tier}
          </span>
          <span style={{ width: 64, fontWeight: 600 }}>{c.substation_id}</span>
          <div className="bar-wrap">
            <div className="bar" style={{ width: `${Math.min(100, c.priority_score ?? 0)}%` }} />
          </div>
          <span className="score">{(c.priority_score ?? 0).toFixed(1)}</span>
        </div>
      ))}
      <div className="note">점수 = 100×(0.55×risk + 0.30×leadtime_urgency + 0.15×group_weight) — 정책 점수(비 ML)</div>
    </div>
  )
}
