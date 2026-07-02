import type { ReplayStatus } from '../types'

export default function ReplayClock({ status }: { status: ReplayStatus | null }) {
  const vt = status?.virtual_time ? new Date(status.virtual_time) : null
  return (
    <div className="clock">
      <span className="vtime">
        {vt ? vt.toISOString().replace('T', ' ').slice(0, 16) : '--:--'}
      </span>
      <span className={`badge ${status?.running ? '' : 'stopped'}`}>
        {status?.running ? `재생 중 ×${status?.speed_factor ?? '-'}` : '정지'}
      </span>
    </div>
  )
}
