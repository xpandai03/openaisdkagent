"""
Mock Computer implementation for OpenAI ComputerTool
"""

import base64
import logging
from typing import Literal
from agents import Computer

logger = logging.getLogger(__name__)


class MockComputer(Computer):
    """Mock computer that simulates desktop actions without actually controlling anything"""
    
    def __init__(self):
        self.screen_width = 1920
        self.screen_height = 1080
        self.current_x = 960
        self.current_y = 540
        logger.info("MockComputer initialized")
    
    @property
    def dimensions(self) -> tuple[int, int]:
        """Return screen dimensions"""
        return (self.screen_width, self.screen_height)
    
    @property
    def environment(self) -> str:
        """Return environment type"""
        return "mock"
    
    @property  
    def type(self) -> str:
        """Return computer type"""
        return "desktop"
    
    def wait(self, seconds: float) -> None:
        """Wait for the specified number of seconds"""
        import time
        time.sleep(seconds)
    
    def screenshot(self) -> str:
        """Return a mock screenshot as base64"""
        # Create a simple placeholder image (1x1 transparent PNG)
        # In production, this would capture the actual screen
        logger.info("Taking mock screenshot")
        
        # This is a minimal transparent PNG
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\xfb\x0c\x9d\x00\x00\x00\x00IEND\xaeB`\x82'
        
        # Return base64 encoded image
        return f"data:image/png;base64,{base64.b64encode(png_data).decode()}"
    
    def click(self, x: int, y: int, button: Literal['left', 'right', 'wheel', 'back', 'forward']) -> None:
        """Simulate a click at the given coordinates"""
        logger.info(f"Mock click at ({x}, {y}) with {button} button")
        self.current_x = x
        self.current_y = y
    
    def double_click(self, x: int, y: int) -> None:
        """Simulate a double click"""
        logger.info(f"Mock double-click at ({x}, {y})")
        self.current_x = x
        self.current_y = y
    
    def move(self, x: int, y: int) -> None:
        """Move the cursor to the given coordinates"""
        logger.info(f"Mock move cursor to ({x}, {y})")
        self.current_x = x
        self.current_y = y
    
    def drag(self, path: list[tuple[int, int]]) -> None:
        """Drag along the given path"""
        logger.info(f"Mock drag with {len(path)} points")
        if path:
            self.current_x, self.current_y = path[-1]
    
    def keypress(self, keys: list[str]) -> None:
        """Simulate keypresses"""
        logger.info(f"Mock keypress: {keys}")
    
    def scroll(self, x: int, y: int, direction: Literal['up', 'down'], amount: int) -> None:
        """Simulate scrolling"""
        logger.info(f"Mock scroll at ({x}, {y}): {direction} by {amount}")
    
    def type_text(self, text: str) -> None:
        """Type the given text"""
        logger.info(f"Mock type text: {text[:50]}...")