"""
FastAPI HTTP bridge for LIVE computer use mode
This is a scaffold that returns 501 Not Implemented
Real browser integration would be added here later
"""

import logging
import io
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from PIL import Image, ImageDraw, ImageFont
import uvicorn

logger = logging.getLogger(__name__)

# Create FastAPI app for the bridge
bridge_app = FastAPI(
    title="Computer Use Live Bridge",
    description="HTTP bridge for computer control actions (scaffold)",
    version="0.1.0"
)


class ActionRequest(BaseModel):
    """Request model for computer actions"""
    type: str  # navigate, click, type, scroll, etc.
    selector: Optional[str] = None
    text: Optional[str] = None
    url: Optional[str] = None
    direction: Optional[str] = None
    x: Optional[int] = None
    y: Optional[int] = None


class ActionResponse(BaseModel):
    """Response model for computer actions"""
    success: bool
    message: str
    state: Dict[str, Any]


@bridge_app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Computer Use Live Bridge",
        "status": "scaffold",
        "endpoints": {
            "/health": "Check bridge health",
            "/action": "Execute browser action (501 Not Implemented)",
            "/screenshot": "Get current screenshot"
        }
    }


@bridge_app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "ok": True,
        "mode": "LIVE",
        "status": "scaffold",
        "message": "Bridge is running but browser integration not implemented"
    }


@bridge_app.post("/action", response_model=ActionResponse)
async def execute_action(request: ActionRequest):
    """
    Execute a browser action
    Currently returns 501 Not Implemented
    """
    logger.info(f"LIVE Bridge received action: {request.type} - {request.dict()}")
    
    # For now, return 501 Not Implemented
    raise HTTPException(
        status_code=501,
        detail={
            "error": "Not Implemented",
            "message": "Live browser integration is not yet implemented",
            "action": request.type,
            "note": "Use COMPUTER_MODE=MOCK for testing"
        }
    )
    
    # When implemented, this would:
    # 1. Connect to a real browser (Playwright/Selenium)
    # 2. Execute the action
    # 3. Take a screenshot
    # 4. Return the result


@bridge_app.get("/screenshot")
async def get_screenshot():
    """
    Get current browser screenshot
    Returns a placeholder image for now
    """
    # Generate placeholder screenshot
    width, height = 1024, 640
    img = Image.new('RGB', (width, height), color='#f0f0f0')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
    except:
        font = ImageFont.load_default()
    
    # Draw placeholder content
    draw.rectangle([(0, 0), (width, 60)], fill='#ef4444')
    draw.text((20, 15), "LIVE Bridge - Not Implemented", fill='white', font=font)
    
    draw.text((30, 100), "Live browser integration is not yet implemented.", fill='#374151', font=font)
    draw.text((30, 140), "This is a scaffold that returns 501 for all actions.", fill='#374151', font=font)
    draw.text((30, 180), "Use COMPUTER_MODE=MOCK for testing.", fill='#374151', font=font)
    
    draw.text((30, 250), "To implement:", fill='#6b7280', font=font)
    draw.text((50, 290), "1. Add Playwright or Selenium", fill='#6b7280')
    draw.text((50, 320), "2. Connect to headful browser", fill='#6b7280')
    draw.text((50, 350), "3. Execute real actions", fill='#6b7280')
    draw.text((50, 380), "4. Capture real screenshots", fill='#6b7280')
    
    # Convert to bytes
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return Response(
        content=buffer.getvalue(),
        media_type="image/png",
        headers={"X-Bridge-Status": "scaffold"}
    )


@bridge_app.post("/reset")
async def reset_browser():
    """Reset browser state"""
    return {
        "success": True,
        "message": "Browser reset (no-op in scaffold mode)"
    }


def run_bridge(host: str = "127.0.0.1", port: int = 34115):
    """Run the bridge server"""
    logger.info(f"Starting Computer Use Live Bridge on {host}:{port}")
    logger.warning("This is a scaffold - browser actions will return 501 Not Implemented")
    uvicorn.run(bridge_app, host=host, port=port)


if __name__ == "__main__":
    import sys
    import os
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get port from environment or use default
    port = int(os.getenv("COMPUTER_BRIDGE_PORT", "34115"))
    
    # Run the bridge
    run_bridge(port=port)