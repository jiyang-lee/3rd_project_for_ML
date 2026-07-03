import { useState } from 'react'
import { api } from '../api/client'
import type { Ticket } from '../types'

const statusLabels: Readonly<Record<string, string>> = {
  draft: '초안',
  ready: '검토 완료',
  sent: '전달',
  done: '완료'
}

const nextStatuses: readonly { readonly status: string; readonly label: string }[] = [
  { status: 'ready', label: '검토완료' },
  { status: 'sent', label: '전달' },
  { status: 'done', label: '완료' }
]

type Props = {
  readonly tickets: readonly Ticket[]
  readonly onTicketUpdated: () => void
}

export default function TicketBoard({ tickets, onTicketUpdated }: Props) {
  const [busyTicketId, setBusyTicketId] = useState<number | null>(null)
  const [errorText, setErrorText] = useState<string | null>(null)

  if (tickets.length === 0) {
    return <div className="empty">생성된 티켓이 없습니다.</div>
  }

  const updateStatus = async (ticket: Ticket, status: string) => {
    setBusyTicketId(ticket.ticket_id)
    setErrorText(null)
    try {
      await api.patchTicket(ticket.ticket_id, status)
      onTicketUpdated()
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : '티켓 상태 변경 실패')
    } finally {
      setBusyTicketId(null)
    }
  }

  return (
    <section className="panel table-panel">
      {errorText !== null && <div className="operation-error compact-error">{errorText}</div>}
      <table>
        <thead>
          <tr>
            <th>상태</th>
            <th>의도</th>
            <th>카드</th>
            <th>생성</th>
            <th>본문</th>
            <th>처리</th>
          </tr>
        </thead>
        <tbody>
          {tickets.map((ticket) => (
            <tr key={ticket.ticket_id}>
              <td><span className="status-chip">{statusLabels[ticket.status] ?? ticket.status}</span></td>
              <td>{ticket.intent}</td>
              <td>#{ticket.card_id}</td>
              <td>{new Date(ticket.created_at).toLocaleString('ko-KR')}</td>
              <td className="ticket-text">{ticket.text}</td>
              <td>
                <div className="ticket-actions">
                  {nextStatuses.map((item) => (
                    <button
                      key={item.status}
                      type="button"
                      disabled={busyTicketId !== null || ticket.status === item.status}
                      onClick={() => void updateStatus(ticket, item.status)}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
