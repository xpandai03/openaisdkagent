"""
Fixed WebSocket streaming support using OpenAI Agents SDK
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from agents import Runner
from app.settings import settings

# Set logging to DEBUG for WebSocket debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ConversationManager:
    """Manage conversation sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def get_or_create_session(self, session_id: str = None) -> str:
        """Get or create session"""
        if not session_id:
            # Generate a simple incrementing ID for now
            session_id = f"session-{len(self.sessions) + 1}"
        
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "id": session_id,
                "messages": [],
                "created_at": asyncio.get_event_loop().time()
            }
            logger.info(f"Created new session: {session_id}")
        
        return session_id
    
    def add_message(self, session_id: str, role: str, content: str):
        """Add message to session history"""
        if session_id in self.sessions:
            self.sessions[session_id]["messages"].append({
                "role": role,
                "content": content,
                "timestamp": asyncio.get_event_loop().time()
            })
    
    def get_history(self, session_id: str) -> list:
        """Get session history"""
        if session_id in self.sessions:
            return self.sessions[session_id]["messages"]
        return []


# Global manager
conversation_manager = ConversationManager()


async def stream_agent_response_simple(websocket: WebSocket, task: str, session_id: str):
    """
    Stream agent response with simplified approach
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
        conversation_manager.add_message(session_id, "user", task)
        
        # Send start signal
        await websocket.send_json({
            "type": "stream_start",
            "message": "Processing..."
        })
        
        logger.info(f"Processing task: {task[:50]}...")
        
        try:
            # Try streaming first
            logger.info("Attempting streaming response...")
            result_stream = Runner.run_streamed(
                starting_agent=agent,
                input=task
                # Don't use conversation_id since it requires specific format
            )
            
            full_response = ""
            tool_calls = []
            event_count = 0
            
            # Stream the events
            async for event in result_stream.stream_events():
                event_count += 1
                try:
                    # Log event details for debugging
                    event_type = getattr(event, 'type', None)
                    
                    # Handle raw_response_event which contains the actual events
                    if event_type == 'raw_response_event':
                        # Extract the nested data
                        event_data = getattr(event, 'data', None)
                        if event_data:
                            nested_type = getattr(event_data, 'type', None)
                            
                            # Handle text delta events
                            if nested_type == 'response.output_text.delta':
                                delta_text = getattr(event_data, 'delta', '')
                                if delta_text:
                                    full_response += delta_text
                                    await websocket.send_json({
                                        "type": "text_delta",
                                        "content": delta_text
                                    })
                                    logger.debug(f"Sent text delta: {delta_text}")
                            
                            # Handle tool call events
                            elif nested_type == 'response.tool_call' or 'tool' in nested_type:
                                tool_name = getattr(event_data, 'name', 'Unknown')
                                logger.info(f"Tool called: {tool_name}")
                                tool_calls.append({"name": tool_name, "status": "executed"})
                                
                                # Special handling for ComputerTool
                                tool_data = {"name": tool_name}
                                if tool_name == 'ComputerTool' or 'computer' in tool_name.lower():
                                    # Extract any screenshot or action data
                                    if hasattr(event_data, 'screenshot'):
                                        tool_data['screenshot'] = event_data.screenshot
                                    if hasattr(event_data, 'action'):
                                        tool_data['action'] = event_data.action
                                    if hasattr(event_data, 'coordinates'):
                                        tool_data['coordinates'] = event_data.coordinates
                                    tool_data['type'] = 'computer'
                                    logger.info(f"Computer action detected: {tool_data}")
                                
                                await websocket.send_json({
                                    "type": "tool_call",
                                    "tool": tool_data
                                })
                            
                            # Handle completion
                            elif nested_type == 'response.done':
                                logger.info("Response completed via event")
                                # Response is done, we'll handle final text below
                            
                            # Log other nested event types for debugging
                            else:
                                logger.debug(f"Nested event type: {nested_type}")
                    
                    # Handle direct event types (if they exist)
                    elif event_type == 'text-delta':
                        text = getattr(event, 'text', '')
                        if text:
                            full_response += text
                            await websocket.send_json({
                                "type": "text_delta",
                                "content": text
                            })
                    
                    elif event_type == 'agent-message':
                        content = getattr(event, 'content', '')
                        if content and isinstance(content, str):
                            if not full_response:
                                full_response = content
                                await websocket.send_json({
                                    "type": "text_complete",
                                    "content": content
                                })
                    
                    # Handle other event types
                    elif hasattr(event, 'content'):
                        content = event.content
                        if isinstance(content, str):
                            full_response += content
                            await websocket.send_json({
                                "type": "text_delta",
                                "content": content
                            })
                
                except Exception as event_error:
                    logger.error(f"Event processing error: {event_error}", exc_info=True)
                    continue
                
                await asyncio.sleep(0.01)
            
            logger.info(f"Streamed {event_count} events, response length: {len(full_response)}")
            
            # Get final result if we haven't captured it
            if not full_response:
                logger.warning("No response captured from streaming, trying to get final result...")
                try:
                    # Wait for the stream to complete and get result
                    final_result = await result_stream
                    logger.debug(f"Final result type: {type(final_result)}, attrs: {dir(final_result)}")
                    
                    if hasattr(final_result, 'final_output'):
                        full_response = final_result.final_output
                        logger.info(f"Got final_output: {full_response[:50]}...")
                    elif hasattr(final_result, 'output'):
                        full_response = final_result.output
                        logger.info(f"Got output: {full_response[:50]}...")
                    else:
                        full_response = str(final_result)
                        logger.info(f"Stringified result: {full_response[:50]}...")
                except Exception as final_error:
                    logger.error(f"Failed to get final result: {final_error}")
                    full_response = full_response or "I apologize, but I couldn't generate a proper response."
            
        except Exception as stream_error:
            logger.warning(f"Streaming failed, falling back to regular run: {stream_error}", exc_info=True)
            
            # Fallback to non-streaming
            try:
                logger.info("Attempting non-streaming response...")
                result = await Runner.run(agent, input=task)
                
                logger.debug(f"Run result type: {type(result)}, attrs: {dir(result)}")
                if hasattr(result, '__dict__'):
                    logger.debug(f"Run result data: {result.__dict__}")
                
                # Try multiple ways to extract the response
                if hasattr(result, 'final_output') and result.final_output:
                    full_response = result.final_output
                    logger.info(f"Got final_output from run: {full_response[:50]}...")
                elif hasattr(result, 'output') and result.output:
                    full_response = result.output
                    logger.info(f"Got output from run: {full_response[:50]}...")
                elif hasattr(result, 'messages'):
                    # Check if there are messages in the result
                    for msg in result.messages:
                        if hasattr(msg, 'content'):
                            full_response = msg.content
                            logger.info(f"Got message content: {full_response[:50]}...")
                            break
                elif hasattr(result, 'content'):
                    full_response = result.content
                    logger.info(f"Got content from run: {full_response[:50]}...")
                else:
                    # Last resort - stringify it
                    full_response = str(result)
                    logger.warning(f"Had to stringify result: {full_response[:50]}...")
                
                # Send complete response
                await websocket.send_json({
                    "type": "text_complete",
                    "content": full_response
                })
                
            except Exception as run_error:
                logger.error(f"Regular run also failed: {run_error}", exc_info=True)
                full_response = f"I apologize, but I encountered an error: {str(run_error)}"
                await websocket.send_json({
                    "type": "text_complete",
                    "content": full_response
                })
        
        # Add assistant response to history
        conversation_manager.add_message(session_id, "assistant", full_response)
        
        # Send completion
        await websocket.send_json({
            "type": "stream_complete",
            "final_text": full_response,
            "tool_calls": tool_calls
        })
        
    except Exception as e:
        logger.error(f"Error in stream_agent_response: {e}")
        error_msg = str(e)
        if "api_key" in error_msg.lower():
            error_msg = "API key not configured properly"
        await websocket.send_json({
            "type": "error",
            "error": error_msg
        })


async def handle_websocket_fixed(websocket: WebSocket):
    """
    Handle WebSocket with fixed streaming
    """
    session_id = None
    
    try:
        await websocket.accept()
        
        # Create session
        session_id = conversation_manager.get_or_create_session()
        
        # Send session info
        await websocket.send_json({
            "type": "session_info",
            "session_id": session_id,
            "history": conversation_manager.get_history(session_id)
        })
        
        logger.info(f"Client connected: {session_id}")
        
        while True:
            try:
                # Receive message
                data = await websocket.receive_json()
                
                if data.get("type") == "task":
                    task = data.get("task", "")
                    if task:
                        await stream_agent_response_simple(websocket, task, session_id)
                
                elif data.get("type") == "get_history":
                    history = conversation_manager.get_history(session_id)
                    await websocket.send_json({
                        "type": "history",
                        "messages": history
                    })
                
                elif data.get("type") == "clear_history":
                    if session_id in conversation_manager.sessions:
                        conversation_manager.sessions[session_id]["messages"] = []
                    await websocket.send_json({
                        "type": "history_cleared"
                    })
                
                elif data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received")
                continue
            except Exception as msg_error:
                logger.error(f"Message handling error: {msg_error}")
                continue
                
    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        logger.info(f"WebSocket closed: {session_id}")