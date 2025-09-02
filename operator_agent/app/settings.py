import os
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

STATE_DIR = Path(".state")
STATE_FILE = STATE_DIR / "operator_agent.json"


@dataclass
class Settings:
    """Application settings with sane defaults"""
    
    # OpenAI
    openai_api_key: Optional[str] = None
    openai_vector_store_id: Optional[str] = None
    
    # Airtable
    airtable_api_key: Optional[str] = None
    airtable_base_id: Optional[str] = None
    airtable_table_name: str = "TestTable"
    
    # Computer Use
    computer_mode: str = "MOCK"  # MOCK | LIVE
    computer_bridge_url: str = "http://127.0.0.1:34115"
    
    @classmethod
    def load(cls) -> "Settings":
        """Load settings from environment and state file"""
        settings = cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_vector_store_id=os.getenv("OPENAI_VECTOR_STORE_ID"),
            airtable_api_key=os.getenv("AIRTABLE_API_KEY"),
            airtable_base_id=os.getenv("AIRTABLE_BASE_ID"),
            airtable_table_name=os.getenv("AIRTABLE_TABLE_NAME", "TestTable"),
            computer_mode=os.getenv("COMPUTER_MODE", "MOCK"),
            computer_bridge_url=os.getenv("COMPUTER_BRIDGE_URL", "http://127.0.0.1:34115")
        )
        
        # Load vector store ID from state if not in env
        if not settings.openai_vector_store_id and STATE_FILE.exists():
            try:
                with open(STATE_FILE) as f:
                    state = json.load(f)
                    settings.openai_vector_store_id = state.get("vector_store_id")
            except Exception:
                pass
        
        return settings
    
    def save_vector_store_id(self, store_id: str):
        """Persist vector store ID to state file"""
        STATE_DIR.mkdir(exist_ok=True)
        state = {}
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE) as f:
                    state = json.load(f)
            except Exception:
                pass
        
        state["vector_store_id"] = store_id
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
        
        self.openai_vector_store_id = store_id
    
    @property
    def has_openai(self) -> bool:
        """Check if OpenAI is configured"""
        return bool(self.openai_api_key)
    
    @property
    def has_airtable(self) -> bool:
        """Check if Airtable is fully configured"""
        return all([
            self.airtable_api_key,
            self.airtable_base_id,
            self.airtable_table_name
        ])
    
    @property
    def has_vector_store(self) -> bool:
        """Check if vector store is configured"""
        return bool(self.openai_vector_store_id)


# Global settings instance
settings = Settings.load()