"""
WebSocket support for streaming agent responses
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from app.agents import run_agent
from app.settings import settings

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept and track a new connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a disconnected client"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_json(self, websocket: WebSocket, data: Dict[str, Any]):
        """Send JSON data to a specific client"""
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
    
    async def broadcast(self, data: Dict[str, Any]):
        """Send data to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")


# Global connection manager
manager = ConnectionManager()


async def stream_agent_response(websocket: WebSocket, task: str):
    """
    Stream agent response with tool calls and screenshots
    
    This simulates streaming by breaking the response into chunks
    In a real implementation, you'd integrate with the Agent's streaming API
    """
    try:
        # Send initial acknowledgment
        await manager.send_json(websocket, {
            "type": "start",
            "content": "Processing your request..."
        })
        
        # Simulate tool call notifications
        if "search" in task.lower():
            await manager.send_json(websocket, {
                "type": "tool_call",
                "tool": {
                    "name": "WebSearch",
                    "status": "ok",
                    "summary": "Searching the web..."
                }
            })
            await asyncio.sleep(0.5)  # Simulate processing
        
        if any(word in task.lower() for word in ["open", "click", "navigate"]):
            await manager.send_json(websocket, {
                "type": "tool_call",
                "tool": {
                    "name": "ComputerTool",
                    "status": "ok",
                    "summary": f"Controlling browser in {settings.computer_mode} mode..."
                }
            })
            await asyncio.sleep(0.5)
        
        # Run the actual agent
        result = await run_agent(task)
        
        # Stream the response text word by word
        words = result["final_text"].split()
        chunk_size = 3  # Words per chunk
        
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i+chunk_size])
            await manager.send_json(websocket, {
                "type": "text",
                "content": chunk + " "
            })
            await asyncio.sleep(0.05)  # Small delay for streaming effect
        
        # Send screenshots if Computer Use was involved
        if result.get("computer_mode") and any(tc["name"] == "ComputerTool" for tc in result.get("tool_calls", [])):
            # In a real implementation, get actual screenshots from computer adapter
            await manager.send_json(websocket, {
                "type": "screenshot",
                "screenshot": {
                    "data": "mock_screenshot_base64_data",
                    "format": "png",
                    "action": "navigate"
                }
            })
        
        # Send completion message with final metadata
        await manager.send_json(websocket, {
            "type": "complete",
            "mode_flags": result.get("mode_flags", {}),
            "tool_calls": result.get("tool_calls", [])
        })
        
    except Exception as e:
        logger.error(f"Error in stream_agent_response: {e}")
        await manager.send_json(websocket, {
            "type": "error",
            "error": str(e)
        })


async def handle_websocket(websocket: WebSocket):
    """
    Handle WebSocket connection for streaming agent responses
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_json()
            
            if data.get("type") == "task":
                task = data.get("task", "")
                if task:
                    # Stream the response
                    await stream_agent_response(websocket, task)
            
            elif data.get("type") == "ping":
                # Respond to ping with pong
                await manager.send_json(websocket, {"type": "pong"})
            
            elif data.get("type") == "close":
                break
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)