/**
 * useWebSocket Hook
 *
 * Manages WebSocket connection to AI Orchestrator autonomous loop.
 * Provides real-time event streaming with automatic reconnection.
 * Now includes support for multi-agent orchestration events.
 */

import { useEffect, useState, useCallback, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useTaskStore } from '../stores/taskStore'
import type { AgentType } from '../types/task'

/**
 * WebSocket event structure from autonomous loop
 */
export interface WebSocketEvent {
  type: string
  severity: 'info' | 'warning' | 'error'
  timestamp: string
  data: Record<string, unknown>
}

/**
 * Hook configuration options
 */
export interface UseWebSocketOptions {
  url?: string
  reconnectDelay?: number
  maxReconnectAttempts?: number
  eventHistoryLimit?: number
}

/**
 * Hook return value
 */
export interface UseWebSocketResult {
  isConnected: boolean
  events: WebSocketEvent[]
  lastEvent: WebSocketEvent | null
  reconnectAttempts: number
  sendMessage: (message: string) => void
  clearEvents: () => void
}

const DEFAULT_OPTIONS: Required<UseWebSocketOptions> = {
  url: 'ws://localhost:8080/ws',
  reconnectDelay: 3000,
  maxReconnectAttempts: 10,
  eventHistoryLimit: 100,
}

/**
 * Custom hook for WebSocket connection to autonomous loop monitoring server
 *
 * @param options - Configuration options
 * @returns WebSocket state and controls
 *
 * @example
 * ```tsx
 * const { isConnected, events, lastEvent } = useWebSocket()
 *
 * // Access events
 * events.forEach(event => {
 *   console.log(event.type, event.data)
 * })
 *
 * // Check connection
 * if (isConnected) {
 *   console.log('Connected to autonomous loop')
 * }
 * ```
 */
export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketResult {
  const config = { ...DEFAULT_OPTIONS, ...options }

  const [isConnected, setIsConnected] = useState(false)
  const [events, setEvents] = useState<WebSocketEvent[]>([])
  const [lastEvent, setLastEvent] = useState<WebSocketEvent | null>(null)
  const [reconnectAttempts, setReconnectAttempts] = useState(0)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const queryClient = useQueryClient()

  // Get Zustand store actions for multi-agent events
  const handleAnalyzing = useTaskStore((state) => state.handleAnalyzing)
  const handleSpecialistStarted = useTaskStore((state) => state.handleSpecialistStarted)
  const handleSpecialistIteration = useTaskStore((state) => state.handleSpecialistIteration)
  const handleSpecialistCompleted = useTaskStore((state) => state.handleSpecialistCompleted)
  const handleSynthesis = useTaskStore((state) => state.handleSynthesis)
  const handleVerification = useTaskStore((state) => state.handleVerification)
  const setTaskStatus = useTaskStore((state) => state.setTaskStatus)

  /**
   * Handle incoming WebSocket message
   */
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const data: WebSocketEvent = JSON.parse(event.data)

      // Add to event history (keep last N events)
      setEvents((prev) => {
        const updated = [...prev, data]
        return updated.slice(-config.eventHistoryLimit)
      })

      setLastEvent(data)

      // Update TanStack Query cache based on event type
      switch (data.type) {
        case 'loop_start':
          queryClient.setQueryData(['loopStatus'], {
            status: 'running',
            ...data.data,
          })
          break

        case 'task_start':
          queryClient.setQueryData(['currentTask'], data.data)
          break

        case 'task_complete':
          // Add to verdicts list
          queryClient.setQueryData(['verdicts'], (old: unknown[]) => {
            const verdicts = Array.isArray(old) ? old : []
            return [...verdicts, data.data].slice(-50) // Keep last 50 verdicts
          })

          // Clear current task
          queryClient.setQueryData(['currentTask'], null)
          break

        case 'ralph_verdict':
          queryClient.setQueryData(['verdicts'], (old: unknown[]) => {
            const verdicts = Array.isArray(old) ? old : []
            return [...verdicts, data.data].slice(-50)
          })
          break

        case 'loop_complete':
          queryClient.setQueryData(['loopStatus'], {
            status: 'completed',
            ...data.data,
          })
          queryClient.setQueryData(['currentTask'], null)
          break

        case 'connection_established':
          // Initial connection confirmation
          console.log('✅ WebSocket connected:', data.data)
          break

        // ==================== Multi-Agent Events ====================

        case 'multi_agent_analyzing': {
          const d = data.data as {
            task_id: string
            project: string
            complexity: string
            specialists: string[]
            challenges: string[]
          }
          handleAnalyzing(d.task_id, d.project, d.complexity, d.specialists, d.challenges)
          console.log('🔍 Multi-agent analyzing:', d.task_id)
          break
        }

        case 'specialist_started': {
          const d = data.data as {
            task_id: string
            project: string
            specialist_type: string
            subtask_id: string
            max_iterations: number
          }
          handleSpecialistStarted(
            d.task_id,
            d.project,
            d.specialist_type as AgentType,
            d.subtask_id,
            d.max_iterations
          )
          console.log('🚀 Specialist started:', d.specialist_type, 'for', d.task_id)
          break
        }

        case 'specialist_iteration': {
          const d = data.data as {
            task_id: string
            project: string
            specialist_type: string
            iteration: number
            max_iterations: number
            verdict?: string
            output_summary: string
          }
          handleSpecialistIteration(
            d.task_id,
            d.project,
            d.specialist_type as AgentType,
            d.iteration,
            d.max_iterations,
            d.verdict,
            d.output_summary
          )
          break
        }

        case 'specialist_completed': {
          const d = data.data as {
            task_id: string
            project: string
            specialist_type: string
            status: string
            verdict: string
            iterations_used: number
            duration_seconds?: number
          }
          handleSpecialistCompleted(
            d.task_id,
            d.project,
            d.specialist_type as AgentType,
            d.status,
            d.verdict,
            d.iterations_used,
            d.duration_seconds
          )
          console.log('✅ Specialist completed:', d.specialist_type, d.verdict)
          break
        }

        case 'multi_agent_synthesis': {
          const d = data.data as {
            task_id: string
            project: string
            specialists_completed: number
            specialists_total: number
          }
          handleSynthesis(d.task_id, d.project, d.specialists_completed, d.specialists_total)
          console.log('🔄 Synthesis started:', d.task_id)
          break
        }

        case 'multi_agent_verification': {
          const d = data.data as {
            task_id: string
            project: string
            verdict: string
            summary: string
          }
          handleVerification(d.task_id, d.project, d.verdict, d.summary)
          console.log('✔️ Multi-agent verification:', d.task_id, d.verdict)
          // Invalidate tasks query to refetch latest status
          queryClient.invalidateQueries({ queryKey: ['tasks'] })
          break
        }

        case 'task_status_change': {
          // Generic status change event
          const d = data.data as {
            task_id: string
            status: string
          }
          setTaskStatus(d.task_id, d.status as Parameters<typeof setTaskStatus>[1])
          break
        }

        default:
          console.log('📨 Received event:', data.type, data.data)
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error)
    }
  }, [
    config.eventHistoryLimit,
    queryClient,
    handleAnalyzing,
    handleSpecialistStarted,
    handleSpecialistIteration,
    handleSpecialistCompleted,
    handleSynthesis,
    handleVerification,
    setTaskStatus,
  ])

  /**
   * Connect to WebSocket server
   */
  const connect = useCallback(() => {
    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close()
    }

    console.log(`🔌 Connecting to WebSocket: ${config.url}`)

    const ws = new WebSocket(config.url)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('✅ WebSocket connected')
      setIsConnected(true)
      setReconnectAttempts(0)

      // Clear any pending reconnect timeout
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
        reconnectTimeoutRef.current = null
      }
    }

    ws.onmessage = handleMessage

    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error)
    }

    ws.onclose = (event) => {
      console.log('🔌 WebSocket disconnected:', event.code, event.reason)
      setIsConnected(false)
      wsRef.current = null

      // Attempt reconnection if not manually closed and under max attempts
      if (event.code !== 1000 && reconnectAttempts < config.maxReconnectAttempts) {
        console.log(`🔄 Reconnecting in ${config.reconnectDelay}ms... (attempt ${reconnectAttempts + 1}/${config.maxReconnectAttempts})`)

        reconnectTimeoutRef.current = setTimeout(() => {
          setReconnectAttempts((prev) => prev + 1)
          connect()
        }, config.reconnectDelay)
      } else if (reconnectAttempts >= config.maxReconnectAttempts) {
        console.error('❌ Max reconnection attempts reached. Please refresh the page.')
      }
    }

    return ws
  }, [config.url, config.reconnectDelay, config.maxReconnectAttempts, reconnectAttempts, handleMessage])

  /**
   * Send message to WebSocket server
   */
  const sendMessage = useCallback((message: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(message)
    } else {
      console.warn('⚠️ WebSocket not connected, cannot send message')
    }
  }, [])

  /**
   * Clear event history
   */
  const clearEvents = useCallback(() => {
    setEvents([])
    setLastEvent(null)
  }, [])

  // Connect on mount
  useEffect(() => {
    const ws = connect()

    // Cleanup on unmount
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (ws) {
        ws.close(1000, 'Component unmounted')
      }
    }
  }, [connect])

  return {
    isConnected,
    events,
    lastEvent,
    reconnectAttempts,
    sendMessage,
    clearEvents,
  }
}
