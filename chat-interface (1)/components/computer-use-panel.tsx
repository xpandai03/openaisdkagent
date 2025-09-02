"use client"

import React, { useState } from "react"
import { 
  Monitor, 
  Mouse, 
  Keyboard, 
  Camera,
  Maximize2,
  X,
  ChevronDown,
  ChevronUp,
  Activity
} from "lucide-react"
import { cn } from "@/lib/utils"

interface ComputerAction {
  type: 'screenshot' | 'click' | 'type' | 'scroll' | 'key'
  timestamp: string
  data?: any
  screenshot?: string
  coordinates?: { x: number; y: number }
  text?: string
}

interface ComputerUsePanelProps {
  actions: ComputerAction[]
  isActive: boolean
  className?: string
}

export function ComputerUsePanel({ 
  actions = [], 
  isActive = false,
  className 
}: ComputerUsePanelProps) {
  const [isExpanded, setIsExpanded] = useState(true)
  const [selectedAction, setSelectedAction] = useState<number | null>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)
  
  const latestScreenshot = actions
    .filter(a => a.screenshot)
    .pop()?.screenshot
  
  const getActionIcon = (type: string) => {
    switch(type) {
      case 'screenshot': return <Camera className="w-4 h-4" />
      case 'click': return <Mouse className="w-4 h-4" />
      case 'type': return <Keyboard className="w-4 h-4" />
      default: return <Activity className="w-4 h-4" />
    }
  }
  
  const getActionLabel = (action: ComputerAction) => {
    switch(action.type) {
      case 'screenshot': return 'Screenshot captured'
      case 'click': return `Clicked at (${action.coordinates?.x}, ${action.coordinates?.y})`
      case 'type': return `Typed: "${action.text?.substring(0, 20)}..."`
      case 'scroll': return 'Scrolled page'
      case 'key': return `Pressed ${action.text}`
      default: return 'Action performed'
    }
  }
  
  if (actions.length === 0 && !isActive) {
    return null
  }
  
  return (
    <div className={cn(
      "bg-gray-900 border border-gray-800 rounded-lg overflow-hidden",
      className
    )}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-800/50 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <Monitor className="w-4 h-4 text-blue-400" />
          <span className="text-sm font-medium text-gray-200">
            Computer Use
          </span>
          {isActive && (
            <span className="flex items-center gap-1 text-xs text-green-400">
              <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              Active
            </span>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-1 hover:bg-gray-700 rounded transition-colors"
            title="Fullscreen"
          >
            <Maximize2 className="w-4 h-4 text-gray-400" />
          </button>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 hover:bg-gray-700 rounded transition-colors"
          >
            {isExpanded ? (
              <ChevronUp className="w-4 h-4 text-gray-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-400" />
            )}
          </button>
        </div>
      </div>
      
      {/* Content */}
      {isExpanded && (
        <div className="flex h-96">
          {/* Screenshot Preview */}
          <div className="flex-1 bg-black p-4 flex items-center justify-center">
            {latestScreenshot ? (
              <div className="relative w-full h-full">
                <img 
                  src={latestScreenshot}
                  alt="Computer screen"
                  className="w-full h-full object-contain"
                />
                {/* Action overlay */}
                {selectedAction !== null && actions[selectedAction]?.coordinates && (
                  <div 
                    className="absolute w-4 h-4 -ml-2 -mt-2 border-2 border-red-500 rounded-full animate-pulse"
                    style={{
                      left: `${actions[selectedAction].coordinates!.x}%`,
                      top: `${actions[selectedAction].coordinates!.y}%`
                    }}
                  />
                )}
              </div>
            ) : (
              <div className="text-center text-gray-500">
                <Monitor className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No screenshot available</p>
              </div>
            )}
          </div>
          
          {/* Action Timeline */}
          <div className="w-80 border-l border-gray-800 overflow-y-auto">
            <div className="p-3">
              <h3 className="text-xs font-semibold text-gray-400 uppercase mb-2">
                Action Timeline
              </h3>
              <div className="space-y-1">
                {actions.length === 0 ? (
                  <p className="text-xs text-gray-500 py-2">No actions yet</p>
                ) : (
                  actions.map((action, idx) => (
                    <button
                      key={idx}
                      onClick={() => setSelectedAction(idx)}
                      className={cn(
                        "w-full flex items-start gap-2 p-2 rounded text-left transition-colors",
                        selectedAction === idx 
                          ? "bg-blue-900/30 border border-blue-700" 
                          : "hover:bg-gray-800"
                      )}
                    >
                      <span className="mt-0.5 text-gray-400">
                        {getActionIcon(action.type)}
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-gray-200 truncate">
                          {getActionLabel(action)}
                        </p>
                        <p className="text-xs text-gray-500">
                          {new Date(action.timestamp).toLocaleTimeString()}
                        </p>
                      </div>
                    </button>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Fullscreen Modal */}
      {isFullscreen && latestScreenshot && (
        <div className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-8">
          <button
            onClick={() => setIsFullscreen(false)}
            className="absolute top-4 right-4 p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-white" />
          </button>
          <img 
            src={latestScreenshot}
            alt="Computer screen fullscreen"
            className="max-w-full max-h-full object-contain"
          />
        </div>
      )}
    </div>
  )
}