"""
Real streaming WebSocket support using OpenAI Agents SDK
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from agents import Runner
from app.settings import settings
import uuid

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manage conversation sessions and history"""
    
    def __init__(self):
        # In-memory storage (replace with Redis/DB in production)
        self.conversations: Dict[str, Dict[str, Any]] = {}
    
    def get_or_create_session(self, session_id: str = None) -> str:
        """Get existing session or create new one"""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        if session_id not in self.conversations:
            self.conversations[session_id] = {
                "id": session_id,
                "messages": [],
                "created_at": asyncio.get_event_loop().time()
            }
            logger.info(f"Created new conversation: {session_id}")
        
        return session_id
    
    def add_message(self, session_id: str, role: str, content: str):
        """Add message to conversation history"""
        if session_id in self.conversations:
            self.conversations[session_id]["messages"].append({
                "role": role,
                "content": content,
                "timestamp": asyncio.get_event_loop().time()
            })
    
    def get_history(self, session_id: str) -> list:
        """Get conversation history"""
        if session_id in self.conversations:
            return self.conversations[session_id]["messages"]
        return []


class StreamingConnectionManager:
    """Manage WebSocket connections with streaming"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.conversation_manager = ConversationManager()
    
    async def connect(self, websocket: WebSocket, session_id: str = None) -> str:
        """Accept connection and return session ID"""
        await websocket.accept()
        session_id = self.conversation_manager.get_or_create_session(session_id)
        self.active_connections[session_id] = websocket
        
        # Send session info and history
        history = self.conversation_manager.get_history(session_id)
        await websocket.send_json({
            "type": "session_info",
            "session_id": session_id,
            "history": history
        })
        
        logger.info(f"Client connected: {session_id}")
        return session_id
    
    def disconnect(self, session_id: str):
        """Remove disconnected client"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        logger.info(f"Client disconnected: {session_id}")
    
    async def send_json(self, session_id: str, data: Dict[str, Any]):
        """Send JSON to specific client"""
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json(data)
            except Exception as e:
                logger.error(f"Error sending to {session_id}: {e}")


# Global manager
manager = StreamingConnectionManager()


async def stream_agent_response(websocket: WebSocket, task: str, session_id: str):
    """
    Stream real agent response using OpenAI SDK streaming
    """
    from app.agents import create_agent
    
    try:
        # Get or create agent
        agent = create_agent()
        if not agent:
            await websocket.send_json({
                "type": "error",
                "error": "Failed to initialize agent"
            })
            return
        
        # Add user message to history
        manager.conversation_manager.add_message(session_id, "user", task)
        
        # Send start signal
        await websocket.send_json({
            "type": "stream_start",
            "message": "Processing your request..."
        })
        
        # Use streaming Runner
        logger.info(f"Starting streaming for: {task[:50]}...")
        
        # Get streaming result
        result_stream = Runner.run_streamed(
            starting_agent=agent,
            input=task,
            conversation_id=session_id  # Use session for conversation memory
        )
        
        # Stream the events
        full_response = ""
        tool_calls = []
        
        try:
            # Process streaming events
            async for event in result_stream.stream_events():
                # Handle different event types
                if hasattr(event, 'type'):
                    if event.type == 'text_delta':
                        # Stream text chunks
                        chunk = getattr(event, 'text', '')
                        full_response += chunk
                        await websocket.send_json({
                            "type": "text_delta",
                            "content": chunk
                        })
                    
                    elif event.type == 'tool_call':
                        # Tool execution
                        tool_info = {
                            "name": getattr(event, 'name', 'Unknown'),
                            "status": "executing"
                        }
                        tool_calls.append(tool_info)
                        await websocket.send_json({
                            "type": "tool_call",
                            "tool": tool_info
                        })
                    
                    elif event.type == 'completion':
                        # Stream completed
                        break
                
                # For text content directly
                elif isinstance(event, str):
                    full_response += event
                    await websocket.send_json({
                        "type": "text_delta",
                        "content": event
                    })
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.01)
        
        except Exception as stream_error:
            logger.warning(f"Streaming iteration error: {stream_error}")
            # Fallback to getting the final result
            try:
                final_result = await result_stream.get_result()
                if hasattr(final_result, 'final_output'):
                    full_response = final_result.final_output
                else:
                    full_response = str(final_result)
                
                # Send the complete response at once
                await websocket.send_json({
                    "type": "text_complete",
                    "content": full_response
                })
            except Exception as result_error:
                logger.error(f"Failed to get result: {result_error}")
                full_response = "I encountered an error processing your request."
        
        # Add assistant message to history
        manager.conversation_manager.add_message(session_id, "assistant", full_response)
        
        # Send completion
        await websocket.send_json({
            "type": "stream_complete",
            "final_text": full_response,
            "tool_calls": tool_calls
        })
        
    except Exception as e:
        logger.error(f"Error in stream_agent_response: {e}")
        await websocket.send_json({
            "type": "error",
            "error": str(e)
        })


async def handle_streaming_websocket(websocket: WebSocket):
    """
    Handle WebSocket connection with real streaming
    """
    session_id = None
    
    try:
        # Get session ID from query params or create new
        session_id = await manager.connect(websocket)
        
        while True:
            # Wait for messages
            data = await websocket.receive_json()
            
            if data.get("type") == "task":
                task = data.get("task", "")
                if task:
                    # Stream the response
                    await stream_agent_response(websocket, task, session_id)
            
            elif data.get("type") == "get_history":
                # Send conversation history
                history = manager.conversation_manager.get_history(session_id)
                await websocket.send_json({
                    "type": "history",
                    "messages": history
                })
            
            elif data.get("type") == "clear_history":
                # Clear conversation
                if session_id in manager.conversation_manager.conversations:
                    manager.conversation_manager.conversations[session_id]["messages"] = []
                await websocket.send_json({
                    "type": "history_cleared"
                })
            
            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if session_id:
            manager.disconnect(session_id)