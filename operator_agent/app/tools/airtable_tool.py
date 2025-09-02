import logging
import json
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)


def create_airtable_tool(settings) -> Optional[Dict[str, Any]]:
    """Create an Airtable function tool if configured"""
    
    if not settings.has_airtable:
        return None
    
    async def upsert_airtable_record(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upsert a record to Airtable
        
        Args:
            payload: Dictionary with fields to insert/update
            
        Returns:
            Dict with status and response or error message
        """
        url = f"https://api.airtable.com/v0/{settings.airtable_base_id}/{settings.airtable_table_name}"
        headers = {
            "Authorization": f"Bearer {settings.airtable_api_key}",
            "Content-Type": "application/json"
        }
        
        # Add timestamp if not present
        if "timestamp" not in payload:
            from datetime import datetime
            payload["timestamp"] = datetime.utcnow().isoformat()
        
        data = {
            "fields": payload,
            "typecast": True  # Allow Airtable to coerce types
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=data)
                
                if response.status_code == 200 or response.status_code == 201:
                    result = response.json()
                    logger.info(f"Airtable record created: {result.get('id')}")
                    return {
                        "status": "success",
                        "record_id": result.get("id"),
                        "message": "Record successfully added to Airtable"
                    }
                else:
                    logger.warning(f"Airtable API error: {response.status_code} - {response.text}")
                    return {
                        "status": "error",
                        "message": f"Airtable API returned {response.status_code}: {response.text[:200]}"
                    }
                    
        except httpx.NetworkError as e:
            logger.error(f"Network error calling Airtable: {e}")
            return {
                "status": "error",
                "message": f"Network error: Could not reach Airtable API"
            }
        except Exception as e:
            logger.error(f"Unexpected error with Airtable: {e}")
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}"
            }
    
    # Return as a function tool definition
    return {
        "name": "upsert_airtable_record",
        "description": "Add or update a record in Airtable",
        "function": upsert_airtable_record,
        "parameters": {
            "type": "object",
            "properties": {
                "payload": {
                    "type": "object",
                    "description": "Fields to insert into Airtable"
                }
            },
            "required": ["payload"]
        }
    }


def register_airtable_tool(agent, settings):
    """Register the Airtable tool with an agent if configured"""
    if not settings.has_airtable:
        logger.info("Airtable not configured - skipping tool registration")
        return False
    
    tool = create_airtable_tool(settings)
    if tool and hasattr(agent, 'tools'):
        # For OpenAI Agents SDK, we need to create a FunctionTool
        try:
            from agents import FunctionTool
            airtable_function = FunctionTool(
                name=tool["name"],
                description=tool["description"],
                function=tool["function"]
            )
            agent.tools.append(airtable_function)
            logger.info("Airtable tool registered with agent")
            return True
        except Exception as e:
            logger.warning(f"Could not register Airtable tool: {e}")
            return False
    
    return False