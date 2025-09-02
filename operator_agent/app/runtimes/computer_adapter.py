"""
Computer adapter that switches between MOCK and LIVE modes
Provides a unified interface for the ComputerTool
"""

import logging
import base64
from typing import Dict, Any, Optional, Tuple
import httpx
from app.settings import settings
from app.runtimes.computer_stub import get_computer_stub

logger = logging.getLogger(__name__)


class ComputerAdapter:
    """Adapter for computer operations that switches between MOCK and LIVE modes"""
    
    def __init__(self, mode: str = None, bridge_url: str = None):
        """
        Initialize the computer adapter
        
        Args:
            mode: Computer mode (MOCK or LIVE), defaults to settings
            bridge_url: URL for LIVE bridge, defaults to settings
        """
        self.mode = mode or settings.computer_mode
        self.bridge_url = bridge_url or settings.computer_bridge_url
        self.stub = get_computer_stub() if self.mode == "MOCK" else None
        
        logger.info(f"Computer adapter initialized in {self.mode} mode")
        if self.mode == "LIVE":
            logger.info(f"Bridge URL: {self.bridge_url}")
    
    async def execute_action(self, action_type: str, **params) -> Dict[str, Any]:
        """
        Execute a computer action
        
        Args:
            action_type: Type of action (navigate, click, type, etc.)
            **params: Parameters for the action
            
        Returns:
            Dict with result including screenshot and state
        """
        if self.mode == "MOCK":
            return await self._mock_execute(action_type, params)
        else:
            return await self._live_execute(action_type, params)
    
    async def _mock_execute(self, action_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action in MOCK mode"""
        try:
            screenshot_bytes, state = await self.stub.execute_action(action_type, params)
            
            # Encode screenshot as base64 for JSON serialization
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            return {
                "success": True,
                "screenshot": screenshot_b64,
                "screenshot_format": "png",
                "state": state,
                "mode": "MOCK"
            }
        except Exception as e:
            logger.error(f"Mock execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "mode": "MOCK"
            }
    
    async def _live_execute(self, action_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action in LIVE mode via HTTP bridge"""
        try:
            async with httpx.AsyncClient() as client:
                # Prepare request data
                request_data = {
                    "type": action_type,
                    **params
                }
                
                # Call the bridge
                response = await client.post(
                    f"{self.bridge_url}/action",
                    json=request_data,
                    timeout=30.0
                )
                
                if response.status_code == 501:
                    # Not implemented - expected for scaffold
                    logger.warning("LIVE bridge returned 501 Not Implemented")
                    return {
                        "success": False,
                        "error": "Live mode not implemented",
                        "message": "Use COMPUTER_MODE=MOCK for testing",
                        "mode": "LIVE"
                    }
                
                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Bridge returned {response.status_code}",
                        "details": response.text,
                        "mode": "LIVE"
                    }
                
                # Get screenshot
                screenshot_response = await client.get(f"{self.bridge_url}/screenshot")
                screenshot_b64 = base64.b64encode(screenshot_response.content).decode('utf-8')
                
                result = response.json()
                return {
                    "success": result.get("success", False),
                    "screenshot": screenshot_b64,
                    "screenshot_format": "png",
                    "state": result.get("state", {}),
                    "mode": "LIVE"
                }
                
        except httpx.ConnectError:
            logger.error(f"Cannot connect to LIVE bridge at {self.bridge_url}")
            return {
                "success": False,
                "error": "Cannot connect to LIVE bridge",
                "message": f"Ensure bridge is running at {self.bridge_url}",
                "mode": "LIVE"
            }
        except Exception as e:
            logger.error(f"LIVE execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "mode": "LIVE"
            }
    
    async def get_screenshot(self) -> Optional[bytes]:
        """Get current screenshot"""
        if self.mode == "MOCK":
            # Generate a current state screenshot
            screenshot, _ = await self.stub.execute_action("screenshot", {})
            return screenshot
        else:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.bridge_url}/screenshot")
                    if response.status_code == 200:
                        return response.content
            except Exception as e:
                logger.error(f"Failed to get screenshot: {e}")
        return None
    
    async def reset(self):
        """Reset the computer state"""
        if self.mode == "MOCK":
            self.stub.reset()
            logger.info("Mock computer reset")
        else:
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(f"{self.bridge_url}/reset")
                    logger.info("Live bridge reset")
            except Exception as e:
                logger.error(f"Failed to reset bridge: {e}")
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get adapter capabilities"""
        return {
            "mode": self.mode,
            "bridge_url": self.bridge_url if self.mode == "LIVE" else None,
            "available_actions": [
                "navigate",
                "click",
                "type",
                "scroll",
                "screenshot"
            ],
            "max_actions_per_run": 30
        }


# Global adapter instance
_adapter_instance = None

def get_computer_adapter() -> ComputerAdapter:
    """Get or create the computer adapter instance"""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = ComputerAdapter()
    return _adapter_instance


async def computer_tool_function(action: str, **params) -> Dict[str, Any]:
    """
    Function to be used by ComputerTool
    
    This wraps the adapter for use with the OpenAI Agents SDK
    """
    adapter = get_computer_adapter()
    result = await adapter.execute_action(action, **params)
    
    # Format for ComputerTool expectations
    if result.get("success"):
        return {
            "status": "success",
            "screenshot": result.get("screenshot"),
            "state": result.get("state", {}),
            "mode": result.get("mode")
        }
    else:
        return {
            "status": "error",
            "error": result.get("error", "Unknown error"),
            "message": result.get("message", ""),
            "mode": result.get("mode")
        }