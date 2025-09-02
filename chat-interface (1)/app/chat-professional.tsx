"use client"

import "ios-vibrator-pro-max"
import React, { useState, useRef, useEffect, useCallback } from "react"
import {
  Send,
  StopCircle,
  RefreshCw,
  Copy,
  Check,
  Wifi,
  WifiOff,
  Trash2,
  Download,
  Settings,
  Monitor,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"
import { ComputerUsePanel } from "@/components/computer-use-panel"

interface Message {
  id: string
  role: "user" | "assistant" | "system"
  content: string
  timestamp: number
  isStreaming?: boolean
  toolCalls?: any[]
  computerActions?: any[]
}

export default function ChatProfessional() {
  // State
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState("")
  const [isStreaming, setIsStreaming] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [computerActions, setComputerActions] = useState<any[]>([])
  const [showComputerPanel, setShowComputerPanel] = useState(false)
  
  // Refs
  const wsRef = useRef<WebSocket | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()
  const currentStreamRef = useRef<string>("")
  
  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }
  
  useEffect(() => {
    scrollToBottom()
  }, [messages])
  
  // WebSocket connection
  const connectWebSocket = useCallback(() => {
    // Prevent multiple connections
    if (wsRef.current?.readyState === WebSocket.OPEN || 
        wsRef.current?.readyState === WebSocket.CONNECTING) {
      return
    }
    
    try {
      const ws = new WebSocket("ws://localhost:8000/ws")
      
      ws.onopen = () => {
        console.log("WebSocket connected")
        setIsConnected(true)
        
        // Clear any reconnect timeout
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current)
          reconnectTimeoutRef.current = undefined
        }
      }
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          console.log("WebSocket message:", data)
          
          switch (data.type) {
            case "session_info":
              setSessionId(data.session_id)
              // Restore history if available
              if (data.history && data.history.length > 0) {
                const restoredMessages = data.history.map((msg: any) => ({
                  id: `msg-${msg.timestamp}`,
                  role: msg.role === "user" ? "user" : "assistant",
                  content: msg.content,
                  timestamp: msg.timestamp
                }))
                setMessages(restoredMessages)
              }
              break
            
            case "stream_start":
              setIsStreaming(true)
              currentStreamRef.current = ""
              // Add empty assistant message
              setMessages(prev => [...prev, {
                id: `assistant-${Date.now()}`,
                role: "assistant",
                content: "",
                timestamp: Date.now(),
                isStreaming: true
              }])
              break
            
            case "text_delta":
              // Append to current stream
              currentStreamRef.current += data.content
              // Update the last message
              setMessages(prev => {
                const updated = [...prev]
                const lastMsg = updated[updated.length - 1]
                if (lastMsg && lastMsg.role === "assistant" && lastMsg.isStreaming) {
                  lastMsg.content = currentStreamRef.current
                }
                return updated
              })
              break
            
            case "text_complete":
              // Full text received at once
              setMessages(prev => {
                const updated = [...prev]
                const lastMsg = updated[updated.length - 1]
                if (lastMsg && lastMsg.role === "assistant") {
                  lastMsg.content = data.content
                  lastMsg.isStreaming = false
                }
                return updated
              })
              break
            
            case "stream_complete":
              setIsStreaming(false)
              // Mark last message as complete
              setMessages(prev => {
                const updated = [...prev]
                const lastMsg = updated[updated.length - 1]
                if (lastMsg && lastMsg.role === "assistant") {
                  // Use final_text if provided, otherwise keep the streamed content
                  if (data.final_text && data.final_text.trim()) {
                    lastMsg.content = data.final_text
                  } else if (!lastMsg.content && currentStreamRef.current) {
                    // If message is empty but we have streamed content, use it
                    lastMsg.content = currentStreamRef.current
                  }
                  lastMsg.isStreaming = false
                  lastMsg.toolCalls = data.tool_calls
                }
                return updated
              })
              currentStreamRef.current = ""
              break
            
            case "tool_call":
              // Show tool execution
              console.log("Tool executed:", data.tool)
              // Check if it's a computer tool action
              if (data.tool?.name === 'ComputerTool' || data.tool?.type === 'computer') {
                setShowComputerPanel(true)
                const action = {
                  type: data.tool.action || 'action',
                  timestamp: new Date().toISOString(),
                  data: data.tool.params,
                  screenshot: data.tool.screenshot,
                  coordinates: data.tool.coordinates,
                  text: data.tool.text
                }
                setComputerActions(prev => [...prev, action])
              }
              break
            
            case "error":
              setIsStreaming(false)
              // Show error message
              setMessages(prev => [...prev, {
                id: `error-${Date.now()}`,
                role: "system",
                content: `Error: ${data.error}`,
                timestamp: Date.now()
              }])
              break
          }
        } catch (error) {
          console.error("Failed to parse WebSocket message:", error)
        }
      }
      
      ws.onerror = (error) => {
        console.error("WebSocket error:", error)
        setIsConnected(false)
      }
      
      ws.onclose = () => {
        console.log("WebSocket disconnected")
        setIsConnected(false)
        setIsStreaming(false)
        wsRef.current = null
        
        // Auto-reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log("Attempting to reconnect...")
          connectWebSocket()
        }, 3000)
      }
      
      wsRef.current = ws
    } catch (error) {
      console.error("Failed to connect WebSocket:", error)
      setIsConnected(false)
    }
  }, [])
  
  // Connect on mount - no dependencies to avoid reconnect loop
  useEffect(() => {
    connectWebSocket()
    
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close()
      }
    }
  }, []) // Remove connectWebSocket from dependencies
  
  // Send message
  const sendMessage = useCallback(() => {
    if (!inputValue.trim() || !isConnected || isStreaming) return
    
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: inputValue.trim(),
      timestamp: Date.now()
    }
    
    // Add user message
    setMessages(prev => [...prev, userMessage])
    
    // Send via WebSocket
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: "task",
        task: inputValue.trim()
      }))
    }
    
    // Clear input
    setInputValue("")
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
    }
    
    // Vibration feedback
    navigator.vibrate?.(50)
  }, [inputValue, isConnected, isStreaming])
  
  // Handle submit
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    sendMessage()
  }
  
  // Handle key down
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }
  
  // Stop generation
  const stopGeneration = () => {
    setIsStreaming(false)
    // Could send stop signal to backend
  }
  
  // Clear chat
  const clearChat = () => {
    setMessages([])
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "clear_history" }))
    }
  }
  
  // Copy message
  const copyMessage = (content: string, id: string) => {
    navigator.clipboard.writeText(content)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }
  
  // Auto-resize textarea
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value)
    
    const textarea = e.target
    textarea.style.height = "auto"
    const newHeight = Math.min(textarea.scrollHeight, 200)
    textarea.style.height = `${newHeight}px`
  }
  
  // Format timestamp
  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
  
  return (
    <div className="flex flex-col h-screen bg-gradient-to-b from-gray-900 to-black text-white">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-gray-800 bg-black/50 backdrop-blur-lg">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-semibold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            AI Assistant
          </h1>
          <div className="flex items-center gap-2">
            {isConnected ? (
              <div className="flex items-center gap-1 text-green-400">
                <Wifi className="w-4 h-4" />
                <span className="text-xs">Connected</span>
              </div>
            ) : (
              <div className="flex items-center gap-1 text-red-400">
                <WifiOff className="w-4 h-4" />
                <span className="text-xs">Disconnected</span>
              </div>
            )}
            {sessionId && (
              <span className="text-xs text-gray-500">
                Session: {sessionId.slice(0, 8)}...
              </span>
            )}
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {computerActions.length > 0 && (
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setShowComputerPanel(!showComputerPanel)}
              className={cn(
                "text-gray-400 hover:text-white",
                showComputerPanel && "text-blue-400"
              )}
              title="Toggle Computer Use panel"
            >
              <Monitor className="w-4 h-4" />
            </Button>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={clearChat}
            className="text-gray-400 hover:text-white"
            title="Clear chat"
          >
            <Trash2 className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="text-gray-400 hover:text-white"
            title="Settings"
          >
            <Settings className="w-4 h-4" />
          </Button>
        </div>
      </header>
      
      {/* Computer Use Panel */}
      {showComputerPanel && (
        <div className="border-b border-gray-800">
          <ComputerUsePanel
            actions={computerActions}
            isActive={isStreaming}
            className="rounded-none"
          />
        </div>
      )}
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 mt-20">
              <p className="text-lg mb-2">Welcome! How can I help you today?</p>
              <p className="text-sm">Type a message below to get started</p>
            </div>
          )}
          
          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "flex gap-4",
                message.role === "user" ? "justify-end" : "justify-start"
              )}
            >
              <div
                className={cn(
                  "group relative max-w-[70%] rounded-2xl px-4 py-3",
                  message.role === "user"
                    ? "bg-blue-600 text-white"
                    : message.role === "system"
                    ? "bg-red-900/50 text-red-200 border border-red-800"
                    : "bg-gray-800 text-gray-100 border border-gray-700"
                )}
              >
                {/* Message content */}
                <div className="whitespace-pre-wrap break-words">
                  {message.content || (message.isStreaming && "...")}
                  {message.isStreaming && (
                    <span className="inline-block w-2 h-4 ml-1 bg-white animate-pulse" />
                  )}
                </div>
                
                {/* Tool calls */}
                {message.toolCalls && message.toolCalls.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {message.toolCalls.map((tool, idx) => (
                      <span
                        key={idx}
                        className="text-xs px-2 py-1 bg-gray-700 rounded-full"
                      >
                        🔧 {tool.name}
                      </span>
                    ))}
                  </div>
                )}
                
                {/* Message actions */}
                <div className="absolute -bottom-8 right-0 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                  <button
                    onClick={() => copyMessage(message.content, message.id)}
                    className="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-white"
                    title="Copy"
                  >
                    {copiedId === message.id ? (
                      <Check className="w-3 h-3" />
                    ) : (
                      <Copy className="w-3 h-3" />
                    )}
                  </button>
                  <span className="text-xs text-gray-500">
                    {formatTime(message.timestamp)}
                  </span>
                </div>
              </div>
            </div>
          ))}
          
          <div ref={messagesEndRef} />
        </div>
      </div>
      
      {/* Input area */}
      <div className="border-t border-gray-800 bg-black/50 backdrop-blur-lg p-4">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
          <div className="relative flex items-end gap-2">
            <div className="flex-1 relative">
              <Textarea
                ref={textareaRef}
                value={inputValue}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder={
                  isStreaming
                    ? "AI is thinking..."
                    : isConnected
                    ? "Type your message..."
                    : "Connecting..."
                }
                disabled={!isConnected || isStreaming}
                className={cn(
                  "w-full min-h-[52px] max-h-[200px] px-4 py-3 pr-12",
                  "bg-gray-800 border-gray-700 text-white placeholder-gray-500",
                  "rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500",
                  "transition-all duration-200",
                  (!isConnected || isStreaming) && "opacity-50 cursor-not-allowed"
                )}
                rows={1}
              />
              
              {/* Character count */}
              {inputValue.length > 0 && (
                <span className="absolute bottom-2 right-14 text-xs text-gray-500">
                  {inputValue.length}
                </span>
              )}
            </div>
            
            {/* Send/Stop button */}
            {isStreaming ? (
              <Button
                type="button"
                onClick={stopGeneration}
                className="h-[52px] px-4 bg-red-600 hover:bg-red-700"
              >
                <StopCircle className="w-5 h-5" />
              </Button>
            ) : (
              <Button
                type="submit"
                disabled={!inputValue.trim() || !isConnected}
                className={cn(
                  "h-[52px] px-4",
                  "bg-gradient-to-r from-blue-600 to-purple-600",
                  "hover:from-blue-700 hover:to-purple-700",
                  "disabled:opacity-50 disabled:cursor-not-allowed",
                  "transition-all duration-200"
                )}
              >
                <Send className="w-5 h-5" />
              </Button>
            )}
          </div>
          
          {/* Tips */}
          <div className="mt-2 text-xs text-gray-500 text-center">
            Press Enter to send • Shift+Enter for new line
          </div>
        </form>
      </div>
    </div>
  )
}