#!/usr/bin/env python3
"""Test WebSocket connection directly"""

import asyncio
import json
import websockets

async def test_websocket():
    uri = "ws://localhost:8000/ws"
    
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket")
        
        # Wait for session info
        response = await websocket.recv()
        data = json.loads(response)
        print(f"Session info: {data}")
        
        # Send a test message
        test_message = {
            "type": "task",
            "task": "What is 2+2?"
        }
        await websocket.send(json.dumps(test_message))
        print("Sent test message")
        
        # Receive responses
        while True:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(response)
                print(f"Received: {data['type']} - {data.get('content', data.get('message', ''))[:100]}")
                
                if data['type'] == 'stream_complete':
                    print(f"Final response: {data.get('final_text', '')}")
                    break
                    
            except asyncio.TimeoutError:
                print("Timeout waiting for response")
                break
            except Exception as e:
                print(f"Error: {e}")
                break

if __name__ == "__main__":
    asyncio.run(test_websocket())