# Operator Agent API

OpenAI Agents SDK implementation with WebSearch, FileSearch, and Computer Use capabilities.

## Quick Start

### 1. Setup Environment

```bash
make setup
```

### 2. Configure API Keys

Copy `.env.example` to `.env` and add your OpenAI API key:

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 3. Activate Virtual Environment

```bash
source .venv/bin/activate
```

### 4. Run the API

```bash
make run
```

The API will be available at http://localhost:8000

## Testing

### Health Check
```bash
curl http://localhost:8000/healthz
```

### Run a Task
```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"task":"What is Python?"}'
```

### Run Smoke Tests
```bash
make smoke
```

## Features

- **WebSearch**: Enabled when OPENAI_API_KEY is configured
- **FileSearch**: Auto-creates vector store on first run (Phase 2)
- **Computer Use**: Currently in MOCK mode (Phase 4)
- **Airtable**: Optional integration when configured
- **MCP Tools**: Optional filesystem tools (Phase 3)

## API Endpoints

- `GET /` - API info
- `GET /healthz` - Health check with capability status
- `POST /run` - Execute a task with the agent
- `GET /docs` - Interactive API documentation

## Running Without API Key

The app runs in demo mode without an OpenAI API key, returning helpful messages about what would happen with proper configuration.

## Development

### Run Tests
```bash
make test
```

### Clean Environment
```bash
make clean
```