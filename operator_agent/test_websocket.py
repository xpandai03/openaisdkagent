#!/usr/bin/env python3
import asyncio
import json
import websockets

async def test_websocket():
    uri = "ws://localhost:8000/ws"
    
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket")
        
        # Send a test task
        task = {
            "type": "task",
            "task": "What is the weather like today?"
        }
        await websocket.send(json.dumps(task))
        print(f"Sent task: {task['task']}")
        
        # Receive messages
        while True:
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(message)
                print(f"Received: {data}")
                
                if data.get("type") == "complete":
                    print("Task completed!")
                    break
                elif data.get("type") == "error":
                    print(f"Error: {data.get('error')}")
                    break
                    
            except asyncio.TimeoutError:
                print("Timeout waiting for response")
                break
            except Exception as e:
                print(f"Error: {e}")
                break

if __name__ == "__main__":
    asyncio.run(test_websocket())