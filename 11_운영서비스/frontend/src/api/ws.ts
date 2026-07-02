import { useEffect, useRef } from 'react'
import type { WsEvent } from '../types'

export function useWebSocket(onEvent: (event: WsEvent) => void) {
  const handlerRef = useRef(onEvent)
  handlerRef.current = onEvent

  useEffect(() => {
    let ws: WebSocket | null = null
    let closed = false
    let retry: number | undefined

    const connect = () => {
      const proto = location.protocol === 'https:' ? 'wss' : 'ws'
      ws = new WebSocket(`${proto}://${location.host}/ws`)
      ws.onmessage = (msg) => {
        try {
          handlerRef.current(JSON.parse(msg.data))
        } catch {
          /* ignore malformed */
        }
      }
      ws.onclose = () => {
        if (!closed) retry = window.setTimeout(connect, 2000)
      }
    }
    connect()
    return () => {
      closed = true
      if (retry) clearTimeout(retry)
      ws?.close()
    }
  }, [])
}
