"use client"

import "ios-vibrator-pro-max"

import type React from "react"
import { useState, useRef, useEffect } from "react"
import {
  Search,
  Plus,
  Lightbulb,
  ArrowUp,
  Menu,
  PenSquare,
  RefreshCcw,
  Copy,
  Share2,
  ThumbsUp,
  ThumbsDown,
  Wifi,
  WifiOff,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"
import { useAgentStream } from "@/hooks/useAgentStream"
import { agentAPI } from "@/lib/api"
import type { ToolCall } from "@/types/agent"

type ActiveButton = "none" | "add" | "deepSearch" | "think"
type MessageType = "user" | "system"

interface Message {
  id: string
  content: string
  type: MessageType
  completed?: boolean
  toolCalls?: ToolCall[]
  screenshots?: any[]
}

export default function ChatInterfaceFixed() {
  const [inputValue, setInputValue] = useState("")
  const [messages, setMessages] = useState<Message[]>([])
  const [activeButton, setActiveButton] = useState<ActiveButton>("none")
  const [hasTyped, setHasTyped] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const chatContainerRef = useRef<HTMLDivElement>(null)
  const [isMobile, setIsMobile] = useState(false)
  const [viewportHeight, setViewportHeight] = useState(0)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const mainContainerRef = useRef<HTMLDivElement>(null)
  
  // WebSocket streaming hook
  const {
    isConnected,
    isStreaming,
    streamBuffer,
    toolCalls,
    screenshots,
    sendTask,
  } = useAgentStream({
    onMessage: (message) => {
      console.log('WebSocket message:', message)
      
      // Handle different message types
      if (message.type === 'start') {
        console.log('Stream started')
      } else if (message.type === 'text' && message.content) {
        // Update the last system message with accumulated content
        setMessages(prev => {
          const lastMsg = prev[prev.length - 1]
          if (lastMsg && lastMsg.type === 'system' && !lastMsg.completed) {
            const updated = [...prev]
            updated[updated.length - 1] = {
              ...lastMsg,
              content: lastMsg.content + message.content
            }
            return updated
          }
          return prev
        })
      } else if (message.type === 'complete') {
        // Mark the message as completed
        setMessages(prev => {
          const lastMsg = prev[prev.length - 1]
          if (lastMsg && lastMsg.type === 'system') {
            const updated = [...prev]
            updated[updated.length - 1] = {
              ...lastMsg,
              completed: true,
              toolCalls: message.tool_calls || []
            }
            return updated
          }
          return prev
        })
      } else if (message.type === 'error') {
        // Show error message
        setMessages(prev => {
          const lastMsg = prev[prev.length - 1]
          if (lastMsg && lastMsg.type === 'system') {
            const updated = [...prev]
            updated[updated.length - 1] = {
              ...lastMsg,
              content: message.error || 'An error occurred',
              completed: true
            }
            return updated
          }
          return prev
        })
      }
    }
  })

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  // Detect mobile
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768 || "ontouchstart" in window)
    }
    checkMobile()
    window.addEventListener("resize", checkMobile)
    return () => window.removeEventListener("resize", checkMobile)
  }, [])

  // Set viewport height
  useEffect(() => {
    const updateViewportHeight = () => {
      setViewportHeight(window.innerHeight)
    }
    updateViewportHeight()
    window.addEventListener("resize", updateViewportHeight)
    return () => window.removeEventListener("resize", updateViewportHeight)
  }, [])

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value
    setInputValue(newValue)

    if (newValue.trim() !== "" && !hasTyped) {
      setHasTyped(true)
    } else if (newValue.trim() === "" && hasTyped) {
      setHasTyped(false)
    }

    // Auto-resize textarea
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = "auto"
      const newHeight = Math.max(24, Math.min(textarea.scrollHeight, 160))
      textarea.style.height = `${newHeight}px`
    }
  }

  const submitMessage = async (userMessage: string) => {
    console.log('Submitting message:', userMessage)
    
    // Add user message
    const userMsg: Message = {
      id: `user-${Date.now()}`,
      content: userMessage,
      type: "user",
    }
    setMessages(prev => [...prev, userMsg])

    // Add empty system message placeholder
    const systemMsg: Message = {
      id: `system-${Date.now()}`,
      content: "",
      type: "system",
      completed: false
    }
    setMessages(prev => [...prev, systemMsg])

    // Send via WebSocket or API
    if (isConnected) {
      console.log('Sending via WebSocket')
      sendTask(userMessage)
    } else {
      console.log('Sending via REST API')
      try {
        const response = await agentAPI.runTask(userMessage)
        console.log('API Response:', response)
        
        // Update the system message with the response
        setMessages(prev => {
          const updated = [...prev]
          updated[updated.length - 1] = {
            ...systemMsg,
            content: response.result,
            completed: true,
            toolCalls: response.steps
          }
          return updated
        })
      } catch (error) {
        console.error('API error:', error)
        setMessages(prev => {
          const updated = [...prev]
          updated[updated.length - 1] = {
            ...systemMsg,
            content: "Sorry, I encountered an error processing your request.",
            completed: true
          }
          return updated
        })
      }
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (inputValue.trim() && !isStreaming) {
      const userMessage = inputValue.trim()
      
      // Clear input
      setInputValue("")
      setHasTyped(false)
      setActiveButton("none")
      
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto"
      }

      // Submit message
      submitMessage(userMessage)

      // Handle focus
      if (!isMobile) {
        textareaRef.current?.focus()
      }
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (!isStreaming && e.key === "Enter" && e.metaKey) {
      e.preventDefault()
      handleSubmit(e)
      return
    }

    if (!isStreaming && !isMobile && e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const toggleButton = (button: ActiveButton) => {
    if (!isStreaming) {
      setActiveButton(prev => prev === button ? "none" : button)
    }
  }

  const renderMessage = (message: Message) => {
    return (
      <div 
        key={message.id} 
        className={cn(
          "flex flex-col gap-2 mb-4",
          message.type === "user" ? "items-end" : "items-start"
        )}
      >
        {/* Message bubble */}
        <div
          className={cn(
            "max-w-[80%] px-4 py-2 rounded-2xl",
            message.type === "user" 
              ? "bg-gray-800 border border-gray-600 rounded-br-none" 
              : "bg-gray-700 rounded-bl-none"
          )}
        >
          <span className="text-white whitespace-pre-wrap">
            {message.content || (message.type === "system" && !message.completed ? "..." : "")}
          </span>
        </div>

        {/* Tool indicators */}
        {message.toolCalls && message.toolCalls.length > 0 && (
          <div className="flex gap-2 px-4">
            {message.toolCalls.map((tool, idx) => (
              <span key={idx} className="text-xs bg-gray-700 px-2 py-1 rounded-full text-gray-300">
                🔧 {tool.name}
              </span>
            ))}
          </div>
        )}

        {/* Message actions */}
        {message.type === "system" && message.completed && (
          <div className="flex items-center gap-2 px-4">
            <button className="text-gray-400 hover:text-white transition-colors">
              <RefreshCcw className="h-4 w-4" />
            </button>
            <button className="text-gray-400 hover:text-white transition-colors">
              <Copy className="h-4 w-4" />
            </button>
            <button className="text-gray-400 hover:text-white transition-colors">
              <Share2 className="h-4 w-4" />
            </button>
            <button className="text-gray-400 hover:text-white transition-colors">
              <ThumbsUp className="h-4 w-4" />
            </button>
            <button className="text-gray-400 hover:text-white transition-colors">
              <ThumbsDown className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>
    )
  }

  return (
    <div
      ref={mainContainerRef}
      className="bg-black flex flex-col overflow-hidden"
      style={{ height: isMobile ? `${viewportHeight}px` : "100vh" }}
    >
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 h-12 flex items-center px-4 z-20 bg-black border-b border-gray-800">
        <div className="w-full flex items-center justify-between px-2">
          <Button variant="ghost" size="icon" className="rounded-full h-8 w-8 hover:bg-gray-800">
            <Menu className="h-5 w-5 text-white" />
            <span className="sr-only">Menu</span>
          </Button>

          <div className="flex items-center gap-2">
            <span className="text-white font-semibold">AI Assistant</span>
            {/* Connection status */}
            <div className={cn("flex items-center gap-1", isConnected ? "text-green-500" : "text-red-500")}>
              {isConnected ? <Wifi className="h-4 w-4" /> : <WifiOff className="h-4 w-4" />}
              <span className="text-xs">{isConnected ? "Connected" : "Disconnected"}</span>
            </div>
          </div>

          <Button variant="ghost" size="icon" className="rounded-full h-8 w-8 hover:bg-gray-800">
            <PenSquare className="h-5 w-5 text-white" />
            <span className="sr-only">New Chat</span>
          </Button>
        </div>
      </header>

      {/* Chat messages */}
      <div ref={chatContainerRef} className="flex-grow pb-32 pt-12 px-4 overflow-y-auto">
        <div className="max-w-3xl mx-auto">
          {messages.map(renderMessage)}
          {isStreaming && (
            <div className="flex items-center gap-2 text-gray-400 px-4">
              <div className="animate-pulse">AI is typing...</div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input area */}
      <div className="fixed bottom-0 left-0 right-0 p-4 bg-black border-t border-gray-800">
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
          <div className="relative w-full rounded-3xl border border-gray-600 bg-gray-800 p-3">
            <div className="pb-9">
              <textarea
                ref={textareaRef}
                value={inputValue}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                disabled={isStreaming}
                className="min-h-[24px] max-h-[160px] w-full rounded-3xl border-0 bg-transparent text-white placeholder:text-gray-400 focus:outline-none resize-none overflow-y-auto"
                placeholder="Ask anything..."
              />
            </div>

            <div className="absolute bottom-3 left-3 right-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <button
                    type="button"
                    onClick={() => toggleButton("add")}
                    className={cn(
                      "rounded-full h-8 w-8 flex items-center justify-center transition-colors",
                      activeButton === "add" 
                        ? "bg-gray-600 text-white" 
                        : "bg-gray-700 hover:bg-gray-600 text-gray-300"
                    )}
                  >
                    <Plus className="h-4 w-4" />
                  </button>
                  
                  <button
                    type="button"
                    onClick={() => toggleButton("deepSearch")}
                    className={cn(
                      "rounded-full h-8 px-3 flex items-center gap-1.5 transition-colors",
                      activeButton === "deepSearch"
                        ? "bg-gray-600 text-white"
                        : "bg-gray-700 hover:bg-gray-600 text-gray-300"
                    )}
                  >
                    <Search className="h-4 w-4" />
                    <span className="text-sm">DeepSearch</span>
                  </button>
                  
                  <button
                    type="button"
                    onClick={() => toggleButton("think")}
                    className={cn(
                      "rounded-full h-8 px-3 flex items-center gap-1.5 transition-colors",
                      activeButton === "think"
                        ? "bg-gray-600 text-white"
                        : "bg-gray-700 hover:bg-gray-600 text-gray-300"
                    )}
                  >
                    <Lightbulb className="h-4 w-4" />
                    <span className="text-sm">Think</span>
                  </button>
                </div>

                <button
                  type="submit"
                  disabled={!hasTyped || isStreaming}
                  className={cn(
                    "rounded-full h-8 w-8 flex items-center justify-center transition-all",
                    hasTyped && !isStreaming
                      ? "bg-white text-black hover:bg-gray-200"
                      : "bg-gray-700 text-gray-500 cursor-not-allowed"
                  )}
                >
                  <ArrowUp className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}