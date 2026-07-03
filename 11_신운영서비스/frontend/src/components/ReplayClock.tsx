import { CalendarClock, Pause, Play, RotateCw, Siren } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import type { ReplayScenario, ReplayStatus, ReplayTimeRange } from '../types'

type Props = {
  readonly status: ReplayStatus | null
  readonly onRefresh: () => void
}

export default function ReplayClock({ status, onRefresh }: Props) {
  const [scenarios, setScenarios] = useState<readonly ReplayScenario[]>([])
  const [timeRange, setTimeRange] = useState<ReplayTimeRange | null>(null)
  const [selectedTime, setSelectedTime] = useState('')
  const [selectedScenarioId, setSelectedScenarioId] = useState('')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('시나리오 대기')
  const busyRef = useRef(false)
  const virtualTime = formatDisplayTime(status?.virtual_time)
  const running = status?.running ?? false

  useEffect(() => {
    setSelectedTime(toDatetimeInput(status?.virtual_time))
  }, [status?.virtual_time])

  useEffect(() => {
    let mounted = true
    api.replayScenarios()
      .then((response) => {
        if (!mounted) {
          return
        }
        setScenarios(response.scenarios)
        setTimeRange(response.time_range)
        setMessage(response.time_range.count > 0 ? `${response.time_range.count}개 시점` : '시나리오 없음')
      })
      .catch((error: unknown) => {
        if (error instanceof Error) {
          setMessage('시나리오 로드 실패')
          return
        }
        throw error
      })
    return () => {
      mounted = false
    }
  }, [])

  useEffect(() => {
    const matched = scenarios.find((scenario) => scenario.virtual_time === status?.virtual_time)
    setSelectedScenarioId(matched?.scenario_id ?? '')
  }, [scenarios, status?.virtual_time])

  const runExclusive = useCallback(async (task: () => Promise<void>) => {
    if (busyRef.current) {
      return
    }
    busyRef.current = true
    setBusy(true)
    try {
      await task()
    } finally {
      busyRef.current = false
      setBusy(false)
    }
  }, [])

  const toggle = useCallback(async () => {
    await runExclusive(async () => {
      if (running) {
        await api.replayStop()
        setMessage('정지됨')
      } else {
        await api.replayStart()
        setMessage('자동 진행')
      }
      onRefresh()
    })
  }, [onRefresh, runExclusive, running])

  const tick = useCallback(async () => {
    await runExclusive(async () => {
      const response = await api.replayTick()
      setSelectedTime(toDatetimeInput(response.virtual_time))
      setMessage('다음 시점')
      onRefresh()
    })
  }, [onRefresh, runExclusive])

  const seek = useCallback(
    async (isoTime: string) => {
      await runExclusive(async () => {
        const response = await api.replaySeek(isoTime)
        setSelectedTime(toDatetimeInput(response.virtual_time))
        setMessage('시나리오 이동')
        onRefresh()
      })
    },
    [onRefresh, runExclusive]
  )

  useEffect(() => {
    if (!running) {
      return undefined
    }
    const timer = window.setInterval(() => {
      void tick()
    }, 3500)
    return () => window.clearInterval(timer)
  }, [running, tick])

  const submitSelectedTime = () => {
    if (!selectedTime) {
      return
    }
    void seek(fromDatetimeInput(selectedTime))
  }

  const chooseScenario = (scenarioId: string) => {
    setSelectedScenarioId(scenarioId)
    const scenario = scenarios.find((item) => item.scenario_id === scenarioId)
    if (scenario === undefined) {
      return
    }
    setSelectedTime(toDatetimeInput(scenario.virtual_time))
    void seek(scenario.virtual_time)
  }

  return (
    <div className="clock-widget">
      <div className="clock-readout">
        <span className={running ? 'live-dot running' : 'live-dot'} aria-hidden="true" />
        <strong>{virtualTime}</strong>
        <span>{message}</span>
      </div>
      <input
        aria-label="리플레이 날짜"
        type="datetime-local"
        min={toDatetimeInput(timeRange?.start)}
        max={toDatetimeInput(timeRange?.end)}
        value={selectedTime}
        onChange={(event) => setSelectedTime(event.target.value)}
        disabled={busy}
      />
      <button title="선택 시간으로 이동" onClick={submitSelectedTime} disabled={busy || !selectedTime}>
        <CalendarClock size={14} />
      </button>
      <select
        aria-label="고장 시나리오"
        value={selectedScenarioId}
        onChange={(event) => chooseScenario(event.target.value)}
        disabled={busy || scenarios.length === 0}
      >
        <option value="">고장 시나리오</option>
        {scenarios.map((scenario) => (
          <option key={scenario.scenario_id} value={scenario.scenario_id}>
            {scenario.label}
          </option>
        ))}
      </select>
      <button title={running ? '정지' : '시작'} onClick={() => void toggle()} disabled={busy}>
        {running ? <Pause size={14} /> : <Play size={14} />}
      </button>
      <button title="다음 시점" onClick={() => void tick()} disabled={busy}>
        {running ? <Siren size={14} /> : <RotateCw size={14} />}
      </button>
    </div>
  )
}

function formatDisplayTime(value: string | null | undefined): string {
  if (!value) {
    return '--'
  }
  return new Date(value).toISOString().slice(0, 16).replace('T', ' ')
}

function toDatetimeInput(value: string | null | undefined): string {
  if (!value) {
    return ''
  }
  return new Date(value).toISOString().slice(0, 16)
}

function fromDatetimeInput(value: string): string {
  return `${value}:00.000Z`
}
