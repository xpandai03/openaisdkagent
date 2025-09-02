import logging
import io
import json
from typing import Dict, Any, Tuple
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

logger = logging.getLogger(__name__)


class ComputerStub:
    """Mock computer executor for testing without real browser"""
    
    def __init__(self):
        self.action_count = 0
        self.current_url = "mock://home"
        self.action_history = []
    
    async def execute_action(self, action_type: str, params: Dict[str, Any]) -> Tuple[bytes, Dict[str, Any]]:
        """
        Execute a mock computer action
        
        Args:
            action_type: Type of action (navigate, click, type, scroll, etc.)
            params: Parameters for the action
            
        Returns:
            Tuple of (screenshot_bytes, state_dict)
        """
        self.action_count += 1
        
        # Log the action
        log_entry = {
            "action": action_type,
            "params": params,
            "timestamp": datetime.utcnow().isoformat(),
            "count": self.action_count
        }
        self.action_history.append(log_entry)
        logger.info(f"MOCK Computer Action #{self.action_count}: {action_type} - {params}")
        
        # Update state based on action
        state = self._update_state(action_type, params)
        
        # Generate mock screenshot
        screenshot = self._generate_screenshot(action_type, params, state)
        
        return screenshot, state
    
    def _update_state(self, action_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update internal state based on action"""
        
        notes = []
        
        if action_type == "navigate":
            self.current_url = params.get("url", "mock://unknown")
            notes.append(f"Navigated to {self.current_url}")
        
        elif action_type == "click":
            selector = params.get("selector", "unknown")
            notes.append(f"Clicked on {selector}")
            
            # Simulate navigation after click
            if "cart" in selector.lower():
                self.current_url = "mock://cart"
                notes.append("Navigated to cart page")
            elif "jacket" in selector.lower():
                self.current_url = "mock://product/jacket"
                notes.append("Viewing jacket product page")
        
        elif action_type == "type":
            text = params.get("text", "")
            selector = params.get("selector", "unknown")
            notes.append(f"Typed '{text}' into {selector}")
        
        elif action_type == "scroll":
            direction = params.get("direction", "down")
            notes.append(f"Scrolled {direction}")
        
        else:
            notes.append(f"Performed {action_type} action")
        
        return {
            "url": self.current_url,
            "action_count": self.action_count,
            "last_action": action_type,
            "notes": notes,
            "success": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _generate_screenshot(self, action_type: str, params: Dict[str, Any], state: Dict[str, Any]) -> bytes:
        """Generate a mock screenshot PNG"""
        
        # Create image
        width, height = 1024, 640
        img = Image.new('RGB', (width, height), color='#f5f5f5')
        draw = ImageDraw.Draw(img)
        
        # Try to use a basic font, fall back to default if not available
        try:
            font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
            font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
            font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
        except:
            # Fall back to default font
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Draw header
        draw.rectangle([(0, 0), (width, 60)], fill='#2563eb')
        draw.text((20, 15), "MOCK Browser - Computer Use Simulator", fill='white', font=font_large)
        
        # Draw URL bar
        draw.rectangle([(20, 80), (width-20, 120)], outline='#d1d5db', width=2)
        draw.text((30, 90), f"URL: {state['url']}", fill='#374151', font=font_medium)
        
        # Draw main content area
        y_offset = 150
        
        # Show action performed
        draw.text((30, y_offset), f"Action #{self.action_count}: {action_type.upper()}", 
                 fill='#059669', font=font_large)
        y_offset += 40
        
        # Show parameters
        if params:
            draw.text((30, y_offset), "Parameters:", fill='#6b7280', font=font_medium)
            y_offset += 30
            for key, value in params.items():
                draw.text((50, y_offset), f"• {key}: {value}", fill='#374151', font=font_small)
                y_offset += 25
        
        # Show notes
        if state.get('notes'):
            y_offset += 20
            draw.text((30, y_offset), "Results:", fill='#6b7280', font=font_medium)
            y_offset += 30
            for note in state['notes']:
                draw.text((50, y_offset), f"✓ {note}", fill='#059669', font=font_small)
                y_offset += 25
        
        # Draw footer
        draw.rectangle([(0, height-40), (width, height)], fill='#e5e7eb')
        draw.text((20, height-30), f"Mock Mode | Actions: {self.action_count} | Time: {datetime.now().strftime('%H:%M:%S')}", 
                 fill='#6b7280', font=font_small)
        
        # Add visual elements based on URL
        if "cart" in state['url']:
            # Draw mock cart items
            draw.rectangle([(width-250, 200), (width-50, 400)], outline='#10b981', width=3)
            draw.text((width-230, 220), "Shopping Cart", fill='#10b981', font=font_medium)
            draw.text((width-230, 250), "• Black Jacket", fill='#374151', font=font_small)
            draw.text((width-230, 275), "• Size: Medium", fill='#374151', font=font_small)
            draw.text((width-230, 300), "• Price: $299", fill='#374151', font=font_small)
            
            # Add to cart button (highlighted if just clicked)
            if action_type == "click" and "cart" in str(params.get("selector", "")).lower():
                draw.rectangle([(width-230, 350), (width-70, 385)], fill='#10b981')
                draw.text((width-180, 360), "Added to Cart!", fill='white', font=font_medium)
            else:
                draw.rectangle([(width-230, 350), (width-70, 385)], outline='#10b981', width=2)
                draw.text((width-180, 360), "Add to Cart", fill='#10b981', font=font_medium)
        
        elif "product" in state['url']:
            # Draw mock product page
            draw.rectangle([(50, 250), (350, 450)], fill='#d1d5db')
            draw.text((150, 340), "Jacket Image", fill='#6b7280', font=font_large)
            
            draw.text((400, 260), "Patagonia Black Jacket", fill='#111827', font=font_large)
            draw.text((400, 300), "$299.00", fill='#059669', font=font_medium)
            draw.text((400, 330), "Waterproof • Breathable", fill='#6b7280', font=font_small)
        
        # Convert to bytes
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
    
    def get_history(self) -> list:
        """Get action history"""
        return self.action_history
    
    def reset(self):
        """Reset the stub state"""
        self.action_count = 0
        self.current_url = "mock://home"
        self.action_history = []
        logger.info("Computer stub reset")


# Global instance for reuse
_stub_instance = None

def get_computer_stub() -> ComputerStub:
    """Get or create the computer stub instance"""
    global _stub_instance
    if _stub_instance is None:
        _stub_instance = ComputerStub()
    return _stub_instance