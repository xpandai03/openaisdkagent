// Hook for streaming agent responses via WebSocket

import { useState, useEffect, useCallback, useRef } from 'react'
import type { StreamMessage, ToolCall } from '@/types/agent'

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws'

interface UseAgentStreamOptions {
  onMessage?: (message: StreamMessage) => void
  onComplete?: (toolCalls: ToolCall[]) => void
  onError?: (error: string) => void
  autoReconnect?: boolean
  reconnectDelay?: number
}

export function useAgentStream(options: UseAgentStreamOptions = {}) {
  const {
    onMessage,
    onComplete,
    onError,
    autoReconnect = true,
    reconnectDelay = 3000,
  } = options

  const [isConnected, setIsConnected] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamBuffer, setStreamBuffer] = useState<string>('')
  const [toolCalls, setToolCalls] = useState<ToolCall[]>([])
  const [screenshots, setScreenshots] = useState<any[]>([])
  
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()
  const pingIntervalRef = useRef<NodeJS.Timeout>()

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      const ws = new WebSocket(WS_URL)
      
      ws.onopen = () => {
        console.log('WebSocket connected')
        setIsConnected(true)
        
        // Start ping interval to keep connection alive
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }))
          }
        }, 30000) // Ping every 30 seconds
      }

      ws.onmessage = (event) => {
        try {
          const message: StreamMessage = JSON.parse(event.data)
          
          switch (message.type) {
            case 'start':
              setIsStreaming(true)
              setStreamBuffer('')
              setToolCalls([])
              setScreenshots([])
              break
              
            case 'text':
              if (message.content) {
                setStreamBuffer(prev => prev + message.content)
              }
              break
              
            case 'tool_call':
              if (message.tool) {
                setToolCalls(prev => [...prev, message.tool])
              }
              break
              
            case 'screenshot':
              if (message.screenshot) {
                setScreenshots(prev => [...prev, message.screenshot])
              }
              break
              
            case 'complete':
              setIsStreaming(false)
              if (onComplete) {
                onComplete(toolCalls)
              }
              break
              
            case 'error':
              setIsStreaming(false)
              if (onError && message.error) {
                onError(message.error)
              }
              break
          }
          
          if (onMessage) {
            onMessage(message)
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setIsConnected(false)
        if (onError) {
          onError('WebSocket connection error')
        }
      }

      ws.onclose = () => {
        console.log('WebSocket disconnected')
        setIsConnected(false)
        setIsStreaming(false)
        
        // Clear ping interval
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current)
        }
        
        // Auto-reconnect if enabled
        if (autoReconnect) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect...')
            connect()
          }, reconnectDelay)
        }
      }

      wsRef.current = ws
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
      setIsConnected(false)
      if (onError) {
        onError('Failed to connect to agent server')
      }
    }
  }, [autoReconnect, reconnectDelay, onMessage, onComplete, onError, toolCalls])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current)
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setIsConnected(false)
    setIsStreaming(false)
  }, [])

  const sendTask = useCallback((task: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'task',
        task: task
      }))
      return true
    }
    return false
  }, [])

  // Connect on mount
  useEffect(() => {
    connect()
    
    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  return {
    isConnected,
    isStreaming,
    streamBuffer,
    toolCalls,
    screenshots,
    sendTask,
    connect,
    disconnect,
  }
}