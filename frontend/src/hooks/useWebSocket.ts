import { useEffect, useRef } from 'react'
import type { QueryClient } from '@tanstack/react-query'

const WS_URL = '/ws/analytics'
const MAX_BACKOFF_MS = 30_000

export function useWebSocket(queryClient: QueryClient): void {
  const retryDelay = useRef(1000)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    let unmounted = false

    function connect(): void {
      const ws = new WebSocket(`ws://${window.location.host}${WS_URL}`)
      wsRef.current = ws

      ws.onopen = () => {
        retryDelay.current = 1000
      }

      ws.onmessage = (event: MessageEvent) => {
        try {
          const msg = JSON.parse(event.data as string) as { event: string }
          if (msg.event === 'metrics_updated') {
            void queryClient.invalidateQueries({ queryKey: ['metrics'] })
          }
        } catch {
          // ignore malformed messages
        }
      }

      ws.onclose = () => {
        if (!unmounted) scheduleReconnect()
      }

      ws.onerror = () => {
        ws.close()
      }
    }

    function scheduleReconnect(): void {
      timeoutRef.current = setTimeout(() => {
        if (!unmounted) {
          connect()
          retryDelay.current = Math.min(retryDelay.current * 2, MAX_BACKOFF_MS)
        }
      }, retryDelay.current)
    }

    connect()

    return () => {
      unmounted = true
      if (timeoutRef.current !== null) clearTimeout(timeoutRef.current)
      wsRef.current?.close()
    }
  }, [queryClient])
}
