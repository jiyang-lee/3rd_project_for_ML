import { Building2, FileText, Megaphone, Send, Sparkles } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import type { ActionIntent, ActionResponse, StateCard } from '../types'

const actions: readonly { readonly intent: ActionIntent; readonly label: string; readonly icon: typeof Sparkles }[] = [
  { intent: 'explain_priority', label: '우선순위 설명', icon: Sparkles },
  { intent: 'report', label: '보고서', icon: FileText },
  { intent: 'vendor_message', label: '업체 전달문', icon: Send },
  { intent: 'resident_notice', label: '입주민 공지', icon: Megaphone }
] as const

type Props = {
  readonly card: StateCard | undefined
  readonly onActionComplete: () => void
  readonly onOpenRag: () => void
  readonly onOpenTickets: () => void
}

export default function CardDetail({ card, onActionComplete, onOpenRag, onOpenTickets }: Props) {
  const [result, setResult] = useState<ActionResponse | null>(null)
  const [loadingIntent, setLoadingIntent] = useState<ActionIntent | null>(null)
  const [completedIntent, setCompletedIntent] = useState<ActionIntent | null>(null)
  const [errorText, setErrorText] = useState<string | null>(null)
  const resultRef = useRef<HTMLElement | null>(null)

  useEffect(() => {
    if (result === null) {
      return
    }
    resultRef.current?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  }, [result])

  if (card === undefined) {
    return <div className="empty">카드를 선택하거나 리플레이를 실행하세요.</div>
  }

  const runAction = async (intent: ActionIntent) => {
    setLoadingIntent(intent)
    setErrorText(null)
    try {
      const response = await api.action(card.card_id, intent)
      setResult(response)
      setCompletedIntent(intent)
      onActionComplete()
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : 'LLM 액션 생성 실패')
    } finally {
      setLoadingIntent(null)
    }
  }

  const createsTicket = completedIntent === 'report' || completedIntent === 'vendor_message' || completedIntent === 'resident_notice'

  return (
    <div className="panel-stack">
      <section className="card-detail panel">
        <div className="section-title">
          <Building2 size={17} />
          <h2>{card.substation_id}</h2>
          <span className={`tier-chip ${card.priority_tier}`}>{card.priority_tier}</span>
        </div>
        <div className="detail-grid">
          <Field label="점수" value={card.priority_score?.toFixed(1) ?? '-'} />
          <Field label="위험확률" value={card.risk_probability?.toFixed(3) ?? '-'} />
          <Field label="고장군" value={card.fault_group} />
          <Field label="리드타임" value={card.leadtime_label} />
          <Field label="pre-event" value={card.pre_event_detected} />
          <Field label="검증" value={card.validation_level} />
        </div>
        <p className="reason">{card.why_reason || '판단 사유 없음'}</p>
      </section>

      <section className="panel operator-strip" aria-label="운영 흐름">
        <div>
          <span>다음 판단</span>
          <strong>{card.priority_tier === 'urgent' || card.priority_tier === 'high' ? '조치 초안 생성 후 티켓 검토' : '근거 확인 후 관찰 유지'}</strong>
        </div>
        <button className="action-button compact" onClick={onOpenRag}>
          <FileText size={16} />
          <span>문서 근거 질문</span>
        </button>
      </section>

      <section className="panel">
        <div className="action-grid">
          {actions.map((item) => {
            const Icon = item.icon
            return (
              <button key={item.intent} className="action-button" onClick={() => void runAction(item.intent)} disabled={loadingIntent !== null}>
                <Icon size={16} />
                <span>{loadingIntent === item.intent ? '생성 중' : item.label}</span>
              </button>
            )
          })}
        </div>
      </section>

      {errorText !== null && <section className="panel operation-error">{errorText}</section>}

      {result !== null && (
        <section className="panel generated" ref={resultRef}>
          <div className="generated-toolbar">
            <strong>{createsTicket ? '티켓 초안 생성됨' : 'LLM 결과 생성됨'}</strong>
            <div>
              {createsTicket && (
                <button className="action-button compact" onClick={onOpenTickets}>
                  <FileText size={16} />
                  <span>티켓 보기</span>
                </button>
              )}
              <button className="action-button compact" onClick={onOpenRag}>
                <Sparkles size={16} />
                <span>근거 질문</span>
              </button>
            </div>
          </div>
          <div className="generated-head">
            <span>{result.generated_by}</span>
            <span>{result.cached ? 'cache hit' : `${result.tokens} tokens`}</span>
          </div>
          <pre>{result.text}</pre>
        </section>
      )}
    </div>
  )
}

function Field({ label, value }: { readonly label: string; readonly value: string }) {
  return (
    <div className="field">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}
