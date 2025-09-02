# OpenAI Agents SDK - Production Implementation

A production-ready implementation of OpenAI Agents SDK with WebSearch, FileSearch, Computer Use, MCP, and Airtable integration.

## Features

- ✅ **OpenAI Agents SDK** - Latest SDK with streaming support
- ✅ **WebSearch Tool** - Real-time web search capabilities
- ✅ **FileSearch Tool** - Vector store with automatic bootstrapping
- ✅ **Computer Use** - Browser automation with visual feedback
- ✅ **MCP Integration** - Model Context Protocol support
- ✅ **Airtable Integration** - Database operations
- ✅ **Real-time Streaming** - Character-by-character response streaming
- ✅ **Professional UI** - Next.js chat interface with dark theme

## Architecture

```
├── operator_agent/          # Backend (FastAPI + OpenAI SDK)
│   ├── app/
│   │   ├── main.py         # FastAPI server
│   │   ├── agents.py       # Agent configuration
│   │   ├── websocket_fixed.py  # WebSocket streaming
│   │   └── tools/          # Custom tools
│   └── requirements.txt
│
└── chat-interface/         # Frontend (Next.js)
    ├── app/
    │   ├── page.tsx
    │   └── chat-professional.tsx
    ├── components/
    │   └── computer-use-panel.tsx
    └── package.json
```

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- OpenAI API key

### Backend Setup

```bash
cd operator_agent
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
echo "OPENAI_API_KEY=your-key-here" > .env

# Start server
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd chat-interface
npm install
npm run dev
```

Visit http://localhost:3001

## Configuration

### Environment Variables (.env)

```env
# Required
OPENAI_API_KEY=sk-...

# Optional
OPENAI_VECTOR_STORE_ID=vs_...
AIRTABLE_API_KEY=pat...
AIRTABLE_BASE_ID=app...
AIRTABLE_TABLE_NAME=Records
COMPUTER_MODE=MOCK  # or LIVE
```

## API Endpoints

- `GET /` - API info
- `GET /healthz` - Health check with capabilities
- `POST /run` - Execute task (non-streaming)
- `WS /ws` - WebSocket for streaming responses

## WebSocket Protocol

### Client → Server
```json
{
  "type": "task",
  "task": "Your message here"
}
```

### Server → Client
```json
// Start streaming
{"type": "stream_start", "message": "Processing..."}

// Text chunks
{"type": "text_delta", "content": "H"}
{"type": "text_delta", "content": "e"}

// Tool execution
{"type": "tool_call", "tool": {"name": "WebSearch"}}

// Complete
{"type": "stream_complete", "final_text": "Full response"}
```

## Computer Use

The Computer Use feature provides visual feedback for browser automation:
- Screenshots of actions
- Click/type visualization
- Action timeline
- Fullscreen mode

## Testing

```bash
# Test WebSocket streaming
cd operator_agent
python test_ws.py

# Test Computer Use
python test_computer.py
```

## Production Deployment

1. Use environment variables for all secrets
2. Enable HTTPS/WSS in production
3. Configure CORS for your domain
4. Use a process manager (PM2, systemd)
5. Set up monitoring and logging

## Tech Stack

- **Backend**: FastAPI, OpenAI Agents SDK, uvicorn
- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS
- **Tools**: WebSearch, FileSearch, ComputerTool, MCP, Airtable
- **Streaming**: WebSockets with character-by-character streaming

## License

MIT