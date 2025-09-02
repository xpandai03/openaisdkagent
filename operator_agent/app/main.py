import asyncio
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.agents import run_agent, get_capabilities
from app.settings import settings
from app.startup.vectorstore_bootstrap import bootstrap_vector_store
from app.websocket_fixed import handle_websocket_fixed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Operator Agent API",
    description="OpenAI Agents SDK with WebSearch, FileSearch, and Computer Use",
    version="0.1.0"
)

# Add CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    """Request model for /run endpoint"""
    task: str


class RunResponse(BaseModel):
    """Response model for /run endpoint"""
    result: str
    steps: list
    mode_flags: Dict[str, Any]


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Operator Agent API",
        "status": "running",
        "docs": "/docs",
        "health": "/healthz"
    }


@app.get("/healthz")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint with capability status"""
    capabilities = get_capabilities()
    
    return {
        "ok": True,
        "websearch": capabilities["websearch"],
        "filesearch": capabilities["filesearch"],
        "computer": capabilities["computer"],
        "airtable": capabilities["airtable"],
        "mcp": capabilities["mcp"],
        "api_key_configured": settings.has_openai,
        "vector_store_configured": settings.has_vector_store
    }


@app.post("/run", response_model=RunResponse)
async def run_task(request: RunRequest) -> RunResponse:
    """Run a task with the agent"""
    try:
        logger.info(f"Running task: {request.task[:100]}...")
        
        # Run the agent
        result = await run_agent(request.task)
        
        # Format response
        return RunResponse(
            result=result["final_text"],
            steps=result["tool_calls"],
            mode_flags={
                "mode": result.get("mode", "unknown"),
                "used_file_search": result["used_file_search"],
                "computer_mode": result["computer_mode"]
            }
        )
        
    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Task execution failed: {str(e)}"
        )


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("Starting Operator Agent API")
    logger.info(f"OpenAI configured: {settings.has_openai}")
    logger.info(f"Vector Store configured: {settings.has_vector_store}")
    logger.info(f"Airtable configured: {settings.has_airtable}")
    logger.info(f"Computer Mode: {settings.computer_mode}")
    
    # Bootstrap vector store if needed
    if settings.has_openai and not settings.has_vector_store:
        logger.info("Bootstrapping vector store...")
        store_id = await bootstrap_vector_store()
        if store_id:
            logger.info(f"Vector store ready: {store_id}")
            # Force reload settings to pick up new store ID
            from app import agents
            agents.agent = None  # Reset agent to pick up new vector store
    
    if not settings.has_openai:
        logger.warning(
            "No OPENAI_API_KEY found. Running in demo mode. "
            "Set OPENAI_API_KEY in .env to enable tools."
        )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for streaming agent responses"""
    await handle_websocket_fixed(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)