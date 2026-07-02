import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { StateCard } from '../types'

export default function RiskChart({ history }: { history: StateCard[] }) {
  const data = [...history]
    .reverse()
    .map((c) => ({
      t: c.window_end.slice(5, 16).replace('T', ' '),
      risk: c.risk_probability,
      fault_p: c.fault_probability,
    }))
  return (
    <div>
      <div className="chart-title">risk_probability 추이 (임계 0.6)</div>
      <ResponsiveContainer width="100%" height={180}>
        <LineChart data={data}>
          <CartesianGrid stroke="#334155" strokeDasharray="3 3" />
          <XAxis dataKey="t" tick={{ fontSize: 10, fill: '#94a3b8' }} minTickGap={40} />
          <YAxis domain={[0, 1]} tick={{ fontSize: 10, fill: '#94a3b8' }} />
          <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155' }} />
          <ReferenceLine y={0.6} stroke="#f8fafc" strokeDasharray="4 4" />
          <Line type="monotone" dataKey="risk" name="pre-event risk" stroke="#ef4444" dot={false} connectNulls />
          <Line type="monotone" dataKey="fault_p" name="fault gate" stroke="#f59e0b" dot={false} connectNulls />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
