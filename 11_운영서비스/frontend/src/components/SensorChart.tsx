import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const COLORS = ['#38bdf8', '#f59e0b', '#22c55e', '#a855f7', '#ef4444']

export default function SensorChart({
  signals,
  rows,
}: {
  signals: string[]
  rows: Record<string, any>[]
}) {
  const data = rows.map((r) => ({ ...r, t: String(r.ts).slice(5, 16).replace('T', ' ') }))
  return (
    <div>
      <div className="chart-title">원시 센서 (최근 7일 window)</div>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data}>
          <CartesianGrid stroke="#334155" strokeDasharray="3 3" />
          <XAxis dataKey="t" tick={{ fontSize: 10, fill: '#94a3b8' }} minTickGap={50} />
          <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} />
          <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155' }} />
          {signals.map((s, i) => (
            <Line key={s} type="monotone" dataKey={s} stroke={COLORS[i % COLORS.length]} dot={false} connectNulls />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
