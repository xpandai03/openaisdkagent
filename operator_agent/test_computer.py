#!/usr/bin/env python3
"""Test WebSocket with computer use command"""

import asyncio
import json
import websockets

async def test_computer_use():
    uri = "ws://localhost:8000/ws"
    
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket")
        
        # Wait for session info
        response = await websocket.recv()
        data = json.loads(response)
        print(f"Session info: {data}")
        
        # Send a computer use command
        test_message = {
            "type": "task",
            "task": "Take a screenshot of the current screen"
        }
        await websocket.send(json.dumps(test_message))
        print("Sent computer use command")
        
        # Receive responses
        while True:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                data = json.loads(response)
                event_type = data.get('type')
                
                if event_type == 'text_delta':
                    print(f"Text: {data.get('content', '')}", end='', flush=True)
                elif event_type == 'tool_call':
                    print(f"\n[Tool: {data.get('tool', {}).get('name', 'Unknown')}]")
                elif event_type == 'stream_complete':
                    print(f"\nFinal: {data.get('final_text', '')[:100]}")
                    break
                else:
                    print(f"\nEvent: {event_type}")
                    
            except asyncio.TimeoutError:
                print("\nTimeout waiting for response")
                break
            except Exception as e:
                print(f"\nError: {e}")
                break

if __name__ == "__main__":
    asyncio.run(test_computer_use())