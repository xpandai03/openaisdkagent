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
import { ToolCallDisplay } from "@/components/tool-call-display"
import { ScreenshotViewer } from "@/components/screenshot-viewer"

type ActiveButton = "none" | "add" | "deepSearch" | "think"
type MessageType = "user" | "system"

interface Message {
  id: string
  content: string
  type: MessageType
  completed?: boolean
  newSection?: boolean
  toolCalls?: ToolCall[]
  screenshots?: any[]
}

interface MessageSection {
  id: string
  messages: Message[]
  isNewSection: boolean
  isActive?: boolean
  sectionIndex: number
}

export default function ChatInterfaceConnected() {
  const [inputValue, setInputValue] = useState("")
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const chatContainerRef = useRef<HTMLDivElement>(null)
  const [hasTyped, setHasTyped] = useState(false)
  const [activeButton, setActiveButton] = useState<ActiveButton>("none")
  const [isMobile, setIsMobile] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [messageSections, setMessageSections] = useState<MessageSection[]>([])
  const [viewportHeight, setViewportHeight] = useState(0)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [completedMessages, setCompletedMessages] = useState<Set<string>>(new Set())
  const [activeSectionId, setActiveSectionId] = useState<string | null>(null)
  const inputContainerRef = useRef<HTMLDivElement>(null)
  const mainContainerRef = useRef<HTMLDivElement>(null)
  const [useWebSocket, setUseWebSocket] = useState(true) // Toggle between WS and API
  
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
      // Handle streaming messages
      if (message.type === 'text' && streamBuffer) {
        // Update the current streaming message
        setMessages(prev => {
          const lastMessage = prev[prev.length - 1]
          if (lastMessage && lastMessage.type === 'system' && !lastMessage.completed) {
            return [
              ...prev.slice(0, -1),
              { ...lastMessage, content: streamBuffer }
            ]
          }
          return prev
        })
      }
    },
    onComplete: (finalToolCalls) => {
      // Mark message as completed
      setMessages(prev => {
        const lastMessage = prev[prev.length - 1]
        if (lastMessage && lastMessage.type === 'system') {
          const completedMessage = {
            ...lastMessage,
            completed: true,
            toolCalls: finalToolCalls,
            screenshots: screenshots
          }
          setCompletedMessages(new Set([...completedMessages, lastMessage.id]))
          return [...prev.slice(0, -1), completedMessage]
        }
        return prev
      })
      
      // Vibration feedback
      navigator.vibrate(50)
    },
    onError: (error) => {
      console.error('Agent error:', error)
      // Show error message to user
      setMessages(prev => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          content: `Error: ${error}`,
          type: 'system',
          completed: true
        }
      ])
    }
  })

  // Constants for layout calculations
  const HEADER_HEIGHT = 48
  const INPUT_AREA_HEIGHT = 100
  const TOP_PADDING = 48
  const BOTTOM_PADDING = 128
  const ADDITIONAL_OFFSET = 16

  // Check if device is mobile and get viewport height
  useEffect(() => {
    const checkMobileAndViewport = () => {
      const isMobileDevice = window.innerWidth < 768
      setIsMobile(isMobileDevice)
      const vh = window.innerHeight
      setViewportHeight(vh)

      if (isMobileDevice && mainContainerRef.current) {
        mainContainerRef.current.style.height = `${vh}px`
      }
    }

    checkMobileAndViewport()
    window.addEventListener("resize", checkMobileAndViewport)
    return () => window.removeEventListener("resize", checkMobileAndViewport)
  }, [])

  // Organize messages into sections
  useEffect(() => {
    if (messages.length === 0) {
      setMessageSections([])
      setActiveSectionId(null)
      return
    }

    const sections: MessageSection[] = []
    let currentSection: MessageSection = {
      id: `section-${Date.now()}-0`,
      messages: [],
      isNewSection: false,
      sectionIndex: 0,
    }

    messages.forEach((message) => {
      if (message.newSection) {
        if (currentSection.messages.length > 0) {
          sections.push({ ...currentSection, isActive: false })
        }
        const newSectionId = `section-${Date.now()}-${sections.length}`
        currentSection = {
          id: newSectionId,
          messages: [message],
          isNewSection: true,
          isActive: true,
          sectionIndex: sections.length,
        }
        setActiveSectionId(newSectionId)
      } else {
        currentSection.messages.push(message)
      }
    })

    if (currentSection.messages.length > 0) {
      sections.push(currentSection)
    }

    setMessageSections(sections)
  }, [messages])

  // Focus the textarea on component mount (only on desktop)
  useEffect(() => {
    if (textareaRef.current && !isMobile) {
      textareaRef.current.focus()
    }
  }, [isMobile])

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value

    if (!isStreaming) {
      setInputValue(newValue)

      if (newValue.trim() !== "" && !hasTyped) {
        setHasTyped(true)
      } else if (newValue.trim() === "" && hasTyped) {
        setHasTyped(false)
      }

      const textarea = textareaRef.current
      if (textarea) {
        textarea.style.height = "auto"
        const newHeight = Math.max(24, Math.min(textarea.scrollHeight, 160))
        textarea.style.height = `${newHeight}px`
      }
    }
  }

  const submitToAgent = async (userMessage: string) => {
    // Add vibration when message is submitted
    navigator.vibrate(50)

    const shouldAddNewSection = messages.length > 0
    const newUserMessage: Message = {
      id: `user-${Date.now()}`,
      content: userMessage,
      type: "user",
      newSection: shouldAddNewSection,
    }

    // Add user message
    setMessages(prev => [...prev, newUserMessage])

    // Create system message placeholder
    const systemMessageId = Date.now().toString()
    setMessages(prev => [...prev, {
      id: systemMessageId,
      content: "",
      type: "system",
      completed: false
    }])

    // Add vibration when streaming begins
    setTimeout(() => navigator.vibrate(50), 200)

    if (useWebSocket && isConnected) {
      // Use WebSocket streaming
      sendTask(userMessage)
    } else {
      // Fallback to regular API call
      try {
        const response = await agentAPI.runTask(userMessage)
        
        // Update message with response
        setMessages(prev => prev.map(msg => 
          msg.id === systemMessageId 
            ? { 
                ...msg, 
                content: response.result, 
                completed: true,
                toolCalls: response.steps
              }
            : msg
        ))
        
        setCompletedMessages(prev => new Set(prev).add(systemMessageId))
        navigator.vibrate(50)
      } catch (error) {
        console.error('API error:', error)
        setMessages(prev => prev.map(msg => 
          msg.id === systemMessageId 
            ? { 
                ...msg, 
                content: "Sorry, I encountered an error processing your request.", 
                completed: true 
              }
            : msg
        ))
      }
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (inputValue.trim() && !isStreaming) {
      const userMessage = inputValue.trim()

      // Reset input before starting the AI response
      setInputValue("")
      setHasTyped(false)
      setActiveButton("none")

      if (textareaRef.current) {
        textareaRef.current.style.height = "auto"
      }

      // Submit to agent
      submitToAgent(userMessage)

      // Handle focus
      if (!isMobile) {
        textareaRef.current?.focus()
      } else {
        textareaRef.current?.blur()
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

  const renderToolIcon = (toolName: string) => {
    switch (toolName) {
      case 'WebSearch':
        return '🔍'
      case 'FileSearch':
        return '📁'
      case 'ComputerTool':
        return '🖥️'
      case 'Airtable':
        return '📊'
      case 'MCP':
        return '⚙️'
      default:
        return '🔧'
    }
  }

  const renderMessage = (message: Message) => {
    const isCompleted = completedMessages.has(message.id)

    return (
      <div key={message.id} className={cn("flex flex-col gap-2", message.type === "user" ? "items-end" : "items-start")}>
        {/* Tool calls visualization */}
        {message.toolCalls && message.toolCalls.length > 0 && (
          <div className="w-full max-w-[80%] space-y-2 px-4">
            {message.toolCalls.map((tool, idx) => (
              <ToolCallDisplay 
                key={idx} 
                toolCall={tool}
                isActive={!message.completed && idx === message.toolCalls.length - 1}
              />
            ))}
          </div>
        )}
        
        {/* Screenshots if available */}
        {message.screenshots && message.screenshots.length > 0 && (
          <div className="w-full max-w-[80%] px-4">
            <ScreenshotViewer screenshots={message.screenshots} />
          </div>
        )}
        
        <div
          className={cn(
            "max-w-[80%] px-4 py-2 rounded-2xl",
            message.type === "user" ? "bg-gray-800 border border-gray-600 rounded-br-none text-white" : "text-white",
          )}
        >
          {message.content && (
            <span className={message.type === "system" && !isCompleted ? "animate-fade-in" : ""}>
              {message.content}
            </span>
          )}
        </div>

        {/* Message actions */}
        {message.type === "system" && message.completed && (
          <div className="flex items-center gap-2 px-4 mt-1 mb-2">
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
      style={{ height: isMobile ? `${viewportHeight}px` : "100svh" }}
    >
      <header className="fixed top-0 left-0 right-0 h-12 flex items-center px-4 z-20 bg-black">
        <div className="w-full flex items-center justify-between px-2">
          <Button variant="ghost" size="icon" className="rounded-full h-8 w-8 hover:bg-gray-800">
            <Menu className="h-5 w-5 text-white" />
            <span className="sr-only">Menu</span>
          </Button>

          <div className="flex items-center gap-2">
            <img
              src="/images/emer-med-logo.png"
              alt="EMER MED"
              className="h-6 w-auto object-contain max-w-[120px] sm:max-w-[140px]"
            />
            {/* Connection status indicator */}
            <div className={cn("flex items-center gap-1", isConnected ? "text-green-500" : "text-red-500")}>
              {isConnected ? <Wifi className="h-4 w-4" /> : <WifiOff className="h-4 w-4" />}
            </div>
          </div>

          <Button variant="ghost" size="icon" className="rounded-full h-8 w-8 hover:bg-gray-800">
            <PenSquare className="h-5 w-5 text-white" />
            <span className="sr-only">New Chat</span>
          </Button>
        </div>
      </header>

      <div ref={chatContainerRef} className="flex-grow pb-32 pt-12 px-4 overflow-y-auto">
        <div className="max-w-3xl mx-auto space-y-4">
          {messageSections.map((section) => (
            <div key={section.id}>
              {section.messages.map((message) => renderMessage(message))}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="fixed bottom-0 left-0 right-0 p-4 bg-black">
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
          <div
            ref={inputContainerRef}
            className={cn(
              "relative w-full rounded-3xl border border-gray-600 bg-gray-800 p-3 cursor-text",
              isStreaming && "opacity-80",
            )}
          >
            <div className="pb-9">
              <Textarea
                ref={textareaRef}
                placeholder={isStreaming ? "Waiting for response..." : "Ask Anything"}
                className="min-h-[24px] max-h-[160px] w-full rounded-3xl border-0 bg-transparent text-white placeholder:text-gray-400 placeholder:text-base focus-visible:ring-0 focus-visible:ring-offset-0 text-base pl-2 pr-4 pt-0 pb-0 resize-none overflow-y-auto leading-tight"
                value={inputValue}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
              />
            </div>

            <div className="absolute bottom-3 left-3 right-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    className={cn(
                      "rounded-full h-8 w-8 flex-shrink-0 border-gray-600 bg-gray-800 hover:bg-gray-700 p-0 transition-colors",
                      activeButton === "add" && "bg-gray-700 border-gray-500",
                    )}
                    onClick={() => toggleButton("add")}
                    disabled={isStreaming}
                  >
                    <Plus className={cn("h-4 w-4 text-white", activeButton === "add" && "text-white")} />
                    <span className="sr-only">Add</span>
                  </Button>

                  <Button
                    type="button"
                    variant="outline"
                    className={cn(
                      "rounded-full h-8 px-3 flex items-center border-gray-600 bg-gray-800 hover:bg-gray-700 gap-1.5 transition-colors",
                      activeButton === "deepSearch" && "bg-gray-700 border-gray-500",
                    )}
                    onClick={() => toggleButton("deepSearch")}
                    disabled={isStreaming}
                  >
                    <Search className={cn("h-4 w-4 text-white", activeButton === "deepSearch" && "text-white")} />
                    <span className={cn("text-white text-sm", activeButton === "deepSearch" && "font-medium")}>
                      DeepSearch
                    </span>
                  </Button>

                  <Button
                    type="button"
                    variant="outline"
                    className={cn(
                      "rounded-full h-8 px-3 flex items-center border-gray-600 bg-gray-800 hover:bg-gray-700 gap-1.5 transition-colors",
                      activeButton === "think" && "bg-gray-700 border-gray-500",
                    )}
                    onClick={() => toggleButton("think")}
                    disabled={isStreaming}
                  >
                    <Lightbulb className={cn("h-4 w-4 text-white", activeButton === "think" && "text-white")} />
                    <span className={cn("text-white text-sm", activeButton === "think" && "font-medium")}>Think</span>
                  </Button>
                </div>

                <Button
                  type="submit"
                  variant="outline"
                  size="icon"
                  className={cn(
                    "rounded-full h-8 w-8 border-0 flex-shrink-0 transition-all duration-200",
                    hasTyped ? "bg-black scale-110" : "bg-gray-700",
                  )}
                  disabled={!inputValue.trim() || isStreaming}
                >
                  <ArrowUp className={cn("h-4 w-4 transition-colors", hasTyped ? "text-white" : "text-gray-300")} />
                  <span className="sr-only">Submit</span>
                </Button>
              </div>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}