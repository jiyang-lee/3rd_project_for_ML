import { useEffect, useRef } from 'react'
import type { WsEvent } from '../types'

export function useWebSocket(onEvent: (event: WsEvent) => void): void {
  const handlerRef = useRef(onEvent)
  handlerRef.current = onEvent

  useEffect(() => {
    let websocket: WebSocket | null = null
    let closed = false
    let retry: number | undefined

    const connect = () => {
      const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
      websocket = new WebSocket(`${protocol}://${location.host}/ws`)
      websocket.onmessage = (message) => {
        void message.data
        const parsed: unknown = JSON.parse(String(message.data))
        if (isWsEvent(parsed)) {
          handlerRef.current(parsed)
        }
      }
      websocket.onclose = () => {
        if (!closed) {
          retry = window.setTimeout(connect, 2000)
        }
      }
    }
    connect()
    return () => {
      closed = true
      if (retry !== undefined) {
        window.clearTimeout(retry)
      }
      websocket?.close()
    }
  }, [])
}

function isWsEvent(value: unknown): value is WsEvent {
  return typeof value === 'object' && value !== null && 'type' in value && 'payload' in value
}
