import { Send } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../api/client'
import type { RagChunk, StateCard } from '../types'
import { TIER_LABEL } from '../types'

type ChatMessage = {
  readonly id: string
  readonly role: 'user' | 'assistant'
  readonly text: string
  readonly generatedBy?: string
  readonly tokens?: number
  readonly sources?: readonly RagChunk[]
}

type Props = {
  readonly card: StateCard | undefined
}

export default function RagSearch({ card }: Props) {
  const [query, setQuery] = useState('책임 범위 알려줘')
  const [messages, setMessages] = useState<readonly ChatMessage[]>([])
  const [loading, setLoading] = useState(false)
  const logRef = useRef<HTMLDivElement | null>(null)

  const quickQuestions = useMemo(() => {
    if (card === undefined) {
      return ['열사용시설 책임 구간 기준 요약해줘', '업체 점검 요청 전에 확인할 문서 근거 알려줘', '입주민 공지에 넣어도 되는 표현 알려줘']
    }
    return [
      '열사용시설 점검 기준에서 이 카드에 연결할 근거 알려줘',
      `열사용시설 책임 구간을 ${card.substation_id} 카드와 연결해서 요약해줘`,
      '업체 전달 전에 확인할 점검 항목 알려줘'
    ]
  }, [card])

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  const send = async () => {
    const question = query.trim()
    if (!question || loading) {
      return
    }
    const timestamp = Date.now()
    setLoading(true)
    setQuery('')
    setMessages((current) => [
      ...current,
      { id: `${timestamp}-user`, role: 'user', text: question }
    ])
    try {
      const context = card === undefined ? undefined : `${card.substation_id}, ${card.priority_tier}, ${card.fault_group}, ${card.leadtime_label}`
      const result = await api.ragChat(question, 5, context)
      setMessages((current) => [
        ...current,
        {
          id: `${timestamp}-assistant`,
          role: 'assistant',
          text: result.answer,
          generatedBy: result.generated_by,
          tokens: result.tokens,
          sources: result.sources
        }
      ])
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          id: `${timestamp}-error`,
          role: 'assistant',
          text: error instanceof Error ? `응답 생성 실패: ${error.message}` : '응답 생성 실패'
        }
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="panel rag-panel">
      <header className="rag-context">
        <div>
          <span>선택 카드</span>
          <strong>{card === undefined ? '카드 없음' : `${card.substation_id} · ${TIER_LABEL[card.priority_tier]}`}</strong>
        </div>
        {card !== undefined && <p>{card.fault_group} · {card.leadtime_label}</p>}
      </header>
      <div className="quick-prompts" aria-label="빠른 질문">
        {quickQuestions.map((item) => (
          <button key={item} type="button" onClick={() => setQuery(item)}>
            {item}
          </button>
        ))}
      </div>
      <div className="rag-chat-log" aria-label="RAG 채팅 내역" ref={logRef}>
        {messages.map((message) => (
          <article key={message.id} className={`chat-message ${message.role}`}>
            <div className="message-meta">
              <strong>{message.role === 'user' ? '질문' : '답변'}</strong>
              {message.generatedBy && <span>{message.generatedBy} · {message.tokens} tokens</span>}
            </div>
            <p className="message-text">{message.text}</p>
            {message.sources && message.sources.length > 0 && (
              <details className="rag-sources">
                <summary>근거 {message.sources.length}개</summary>
                {message.sources.map((source) => (
                  <article key={source.chunk_id} className="rag-item">
                    <strong>{source.title}</strong>
                    <span>{source.breadcrumb ?? '문서'}</span>
                    <p>{source.content}</p>
                  </article>
                ))}
              </details>
            )}
          </article>
        ))}
        {messages.length === 0 && <div className="empty">RAG 문서에 질문을 입력하세요.</div>}
      </div>
      <form
        className="chat-input-row"
        onSubmit={(event) => {
          event.preventDefault()
          void send()
        }}
      >
        <textarea
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault()
              void send()
            }
          }}
          aria-label="RAG 질문"
          rows={2}
        />
        <button className="action-button compact" type="submit" disabled={loading}>
          <Send size={16} />
          <span>{loading ? '생성 중' : '질문'}</span>
        </button>
      </form>
    </section>
  )
}
