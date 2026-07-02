import type { AgentRun } from '../types'

export default function AgentTrace({ runs }: { runs: AgentRun[] }) {
  if (runs.length === 0) return <div className="empty">에이전트 실행 이력이 없습니다</div>
  return (
    <div>
      {runs.map((r) => (
        <div className="trace" key={r.run_id}>
          <div>
            <b>run #{r.run_id}</b> · {r.status} · {new Date(r.started_at).toLocaleString('ko-KR')}
            {' · '}트리거 카드 {r.trigger_card_ids?.length ?? 0}건
          </div>
          {r.node_trace && <pre>{JSON.stringify(r.node_trace, null, 2)}</pre>}
          {r.error && <pre style={{ color: '#f87171' }}>{r.error}</pre>}
        </div>
      ))}
    </div>
  )
}
