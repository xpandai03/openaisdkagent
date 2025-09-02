// Types for OpenAI Agents SDK integration

export interface AgentRequest {
  task: string
}

export interface ToolCall {
  name: string
  status: 'ok' | 'error'
  summary: string
}

export interface ModeFlags {
  mode: 'live' | 'demo' | 'error'
  used_file_search: boolean
  computer_mode: 'MOCK' | 'LIVE'
}

export interface AgentResponse {
  result: string
  steps: ToolCall[]
  mode_flags: ModeFlags
}

export interface HealthStatus {
  ok: boolean
  websearch: boolean
  filesearch: boolean
  computer: 'MOCK' | 'LIVE'
  airtable: boolean
  mcp: boolean
  api_key_configured: boolean
  vector_store_configured: boolean
}

export interface StreamMessage {
  type: 'text' | 'tool_call' | 'screenshot' | 'error' | 'complete'
  content?: string
  tool?: ToolCall
  screenshot?: {
    data: string // base64
    format: string
    action?: string
  }
  error?: string
}

export interface AgentConfig {
  apiUrl: string
  wsUrl: string
  timeout?: number
  retryAttempts?: number
}