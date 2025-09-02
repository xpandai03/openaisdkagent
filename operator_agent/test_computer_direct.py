#!/usr/bin/env python3
"""Test ComputerTool directly"""

import asyncio
import json
import websockets

async def test_computer():
    uri = "ws://localhost:8000/ws"
    
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket")
        
        # Wait for session info
        response = await websocket.recv()
        data = json.loads(response)
        print(f"Session: {data.get('session_id')}")
        
        # Send a computer use command
        test_message = {
            "type": "task",
            "task": "Take a screenshot of the desktop and describe what you see"
        }
        await websocket.send(json.dumps(test_message))
        print("Sent screenshot request")
        
        # Collect responses
        tool_calls = []
        text_response = ""
        
        while True:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=20.0)
                data = json.loads(response)
                event_type = data.get('type')
                
                if event_type == 'text_delta':
                    text = data.get('content', '')
                    text_response += text
                    print(text, end='', flush=True)
                    
                elif event_type == 'tool_call':
                    tool = data.get('tool', {})
                    tool_calls.append(tool)
                    print(f"\n\n🔧 TOOL CALLED: {tool.get('name')}")
                    if tool.get('type') == 'computer':
                        print("  ✅ Computer Use detected!")
                        if tool.get('screenshot'):
                            print(f"  📷 Screenshot: {tool.get('screenshot')[:50]}...")
                            
                elif event_type == 'stream_complete':
                    print(f"\n\n✅ Complete")
                    print(f"Tools used: {[t.get('name') for t in tool_calls]}")
                    break
                    
                elif event_type == 'error':
                    print(f"\n❌ Error: {data.get('error')}")
                    break
                    
            except asyncio.TimeoutError:
                print("\n⏱️ Timeout")
                break

if __name__ == "__main__":
    asyncio.run(test_computer())