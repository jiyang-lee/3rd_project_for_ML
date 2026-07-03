import type { CostDaily } from '../types'

export default function CostDashboard({ costs }: { readonly costs: CostDaily | null }) {
  const prompt = costs?.prompt_tokens ?? 0
  const completion = costs?.completion_tokens ?? 0
  const rows = [
    { label: 'Prompt', value: prompt },
    { label: 'Completion', value: completion },
    { label: 'Cache hit', value: costs?.cache_hits ?? 0 }
  ]
  const maxValue = Math.max(...rows.map((row) => row.value), 1)

  return (
    <section className="panel chart-panel">
      <div className="metric-row">
        <Metric label="호출" value={String(costs?.calls ?? 0)} />
        <Metric label="토큰" value={String(prompt + completion)} />
        <Metric label="예상 비용" value={`$${Number(costs?.estimated_cost_usd ?? 0).toFixed(4)}`} />
      </div>
      <div className="token-bars" aria-label="LLM token usage">
        {rows.map((row) => (
          <div className="token-bar-row" key={row.label}>
            <span>{row.label}</span>
            <div className="token-bar-track">
              <div className="token-bar-fill" style={{ width: `${(row.value / maxValue) * 100}%` }} />
            </div>
            <strong>{row.value.toLocaleString()}</strong>
          </div>
        ))}
      </div>
    </section>
  )
}

function Metric({ label, value }: { readonly label: string; readonly value: string }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}
