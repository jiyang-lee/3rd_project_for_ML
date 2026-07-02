import { useState } from 'react'
import { api } from '../api/client'
import type { DispatchOrder } from '../types'

export default function DispatchFeed({
  orders,
  onChanged,
}: {
  orders: DispatchOrder[]
  onChanged: () => void
}) {
  const [expanded, setExpanded] = useState<number | null>(null)
  if (orders.length === 0) return <div className="empty">출동 지시서가 아직 없습니다</div>
  return (
    <div>
      {orders.map((o) => (
        <div className="order" key={o.order_id}>
          <div className="order-head">
            <span className="title">{o.title}</span>
            <span className="gen">{o.generated_by}</span>
            <span className="gen">{o.status}</span>
            {o.status === 'draft' && (
              <button
                onClick={async () => {
                  await api.patchOrder(o.order_id, 'acknowledged')
                  onChanged()
                }}
              >
                확인
              </button>
            )}
            <button onClick={() => setExpanded(expanded === o.order_id ? null : o.order_id)}>
              {expanded === o.order_id ? '접기' : '펼치기'}
            </button>
          </div>
          {expanded === o.order_id && <div className="body">{o.body_markdown}</div>}
        </div>
      ))}
    </div>
  )
}
