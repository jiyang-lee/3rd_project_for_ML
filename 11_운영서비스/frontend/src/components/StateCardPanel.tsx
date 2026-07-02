import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { StateCard } from '../types'
import RiskChart from './RiskChart'
import SensorChart from './SensorChart'

function ProbBar({ label, value, threshold }: { label: string; value: number | null; threshold: number }) {
  const v = value ?? 0
  const over = v >= threshold
  return (
    <div className="prob-bar">
      <div className="label">
        <span>{label}</span>
        <span>{value != null ? value.toFixed(3) : '-'}</span>
      </div>
      <div className="track">
        <div className="fill" style={{ width: `${v * 100}%`, background: over ? '#ef4444' : '#38bdf8' }} />
        <div className="thresh" style={{ left: `${threshold * 100}%` }} />
      </div>
    </div>
  )
}

export default function StateCardPanel({
  substationId,
  latestCard,
}: {
  substationId: string
  latestCard: StateCard | undefined
}) {
  const [history, setHistory] = useState<StateCard[]>([])
  const [readings, setReadings] = useState<{ signals: string[]; rows: Record<string, any>[] } | null>(null)

  useEffect(() => {
    api.cardHistory(substationId).then(setHistory).catch(() => setHistory([]))
    api.readings(substationId).then(setReadings).catch(() => setReadings(null))
  }, [substationId, latestCard?.card_id])

  const card = latestCard ?? history[0]
  return (
    <div className="drawer">
      <h2>
        {substationId} 상태카드
        {card && ` — ${card.primary_state} (${card.sample_id})`}
      </h2>
      {card && (
        <>
          <div className="prob-bars">
            <ProbBar label="fault gate" value={card.fault_probability} threshold={0.5} />
            <ProbBar label="task gate" value={card.task_probability} threshold={0.5} />
            <ProbBar label="activity gate" value={card.activity_probability} threshold={0.5} />
            <ProbBar label="pre-event risk" value={card.risk_probability} threshold={0.6} />
          </div>
          <div className="fields">
            <div className="field"><span className="k">pre_event_detected</span><span className="v">{card.pre_event_detected}</span></div>
            <div className="field"><span className="k">fault_group</span><span className="v">{card.fault_group}</span></div>
            <div className="field"><span className="k">leadtime_label</span><span className="v">{card.leadtime_label}</span></div>
            <div className="field"><span className="k">priority</span><span className="v">{card.priority_tier} ({card.priority_score?.toFixed(1) ?? '-'})</span></div>
            <div className="field"><span className="k">review</span><span className="v">{card.review_flag ? card.review_reasons || 'yes' : 'no'}</span></div>
            <div className="field"><span className="k">coverage</span><span className="v">{card.coverage_rate?.toFixed(3) ?? '-'}</span></div>
            <div className="field"><span className="k">window</span><span className="v">{card.window_start.slice(0, 16)} ~ {card.window_end.slice(0, 16)}</span></div>
            <div className="field"><span className="k">why</span><span className="v">{card.why_reason}</span></div>
          </div>
          <div className="note">
            fault_group은 리플레이 시나리오 메타데이터 기반 (모델 예측 아님) · validation_level: {card.validation_level}
          </div>
        </>
      )}
      <div className="charts">
        {history.length > 1 && <RiskChart history={history} />}
        {readings && readings.rows.length > 0 && <SensorChart signals={readings.signals} rows={readings.rows} />}
      </div>
    </div>
  )
}
