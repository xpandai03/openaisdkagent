import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  Search, 
  FileSearch, 
  Monitor, 
  Database, 
  Terminal,
  Loader2,
  CheckCircle,
  AlertCircle
} from 'lucide-react'
import type { ToolCall } from '@/types/agent'

interface ToolCallDisplayProps {
  toolCall: ToolCall
  isActive?: boolean
}

const toolIcons: Record<string, React.ReactNode> = {
  websearch: <Search className="w-4 h-4" />,
  filesearch: <FileSearch className="w-4 h-4" />,
  computer: <Monitor className="w-4 h-4" />,
  airtable: <Database className="w-4 h-4" />,
  mcp: <Terminal className="w-4 h-4" />,
}

const toolColors: Record<string, string> = {
  websearch: 'bg-blue-500',
  filesearch: 'bg-green-500',
  computer: 'bg-purple-500',
  airtable: 'bg-orange-500',
  mcp: 'bg-gray-500',
}

export function ToolCallDisplay({ toolCall, isActive = false }: ToolCallDisplayProps) {
  const icon = toolIcons[toolCall.name] || <Terminal className="w-4 h-4" />
  const color = toolColors[toolCall.name] || 'bg-gray-500'
  
  const getStatusIcon = () => {
    if (isActive) return <Loader2 className="w-3 h-3 animate-spin" />
    if (toolCall.result) return <CheckCircle className="w-3 h-3 text-green-500" />
    if (toolCall.error) return <AlertCircle className="w-3 h-3 text-red-500" />
    return null
  }
  
  return (
    <Card className={`transition-all ${isActive ? 'border-primary' : ''}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={`p-1.5 rounded ${color} text-white`}>
              {icon}
            </div>
            <CardTitle className="text-sm font-medium">
              {toolCall.displayName || toolCall.name}
            </CardTitle>
          </div>
          <div className="flex items-center gap-2">
            {getStatusIcon()}
            {toolCall.duration && (
              <Badge variant="outline" className="text-xs">
                {toolCall.duration}ms
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="pt-0">
        {toolCall.args && (
          <div className="mb-2">
            <p className="text-xs text-muted-foreground mb-1">Parameters:</p>
            <pre className="text-xs bg-muted p-2 rounded overflow-x-auto">
              {JSON.stringify(toolCall.args, null, 2)}
            </pre>
          </div>
        )}
        
        {toolCall.result && (
          <div className="mb-2">
            <p className="text-xs text-muted-foreground mb-1">Result:</p>
            <div className="text-xs bg-muted p-2 rounded max-h-32 overflow-y-auto">
              {typeof toolCall.result === 'string' 
                ? toolCall.result 
                : JSON.stringify(toolCall.result, null, 2)}
            </div>
          </div>
        )}
        
        {toolCall.error && (
          <div className="mb-2">
            <p className="text-xs text-red-500 mb-1">Error:</p>
            <div className="text-xs bg-red-50 text-red-700 p-2 rounded">
              {toolCall.error}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}