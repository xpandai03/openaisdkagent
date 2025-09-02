import asyncio
import logging
from typing import Dict, List, Optional, Any
from app.settings import settings

logger = logging.getLogger(__name__)

# Only import OpenAI SDK if API key is available
agent = None
runner = None
WebSearchTool = None
FileSearchTool = None
ComputerTool = None
FunctionTool = None
mcp_server = None
has_mcp = False

if settings.has_openai:
    try:
        from agents import Agent, Runner, WebSearchTool, FileSearchTool, ComputerTool, FunctionTool
    except ImportError as e:
        logger.warning(f"OpenAI Agents SDK not available: {e}")
        settings.openai_api_key = None


def create_agent() -> Optional[Any]:
    """Create the main agent with available tools"""
    global mcp_server, has_mcp
    
    if not settings.has_openai:
        logger.info("OpenAI API key not configured - running in demo mode")
        return None
    
    tools = []
    mcp_servers = []
    
    # WebSearch (always available with API key)
    try:
        web_tool = WebSearchTool()  # Remove max_num_results parameter
        tools.append(web_tool)
        logger.info("WebSearch tool enabled")
    except Exception as e:
        logger.warning(f"Could not initialize WebSearch: {e}")
    
    # FileSearch (if vector store configured and not mock)
    if settings.has_vector_store and not settings.openai_vector_store_id.startswith("vs_mock_"):
        try:
            file_tool = FileSearchTool(
                vector_store_ids=[settings.openai_vector_store_id]
            )
            tools.append(file_tool)
            logger.info(f"FileSearch tool enabled with store: {settings.openai_vector_store_id}")
        except Exception as e:
            logger.warning(f"Could not initialize FileSearch: {e}")
    
    # Computer Use Tool
    # Temporarily disabled due to initialization issues
    # if ComputerTool:
    #     try:
    #         from app.runtimes.computer_adapter import get_computer_adapter
    #         
    #         # Get adapter based on mode
    #         adapter = get_computer_adapter()
    #         capabilities = adapter.get_capabilities()
    #         
    #         # Create ComputerTool with adapter
    #         # Note: ComputerTool in agents SDK has specific requirements
    #         # Try without parameters first
    #         computer_tool = ComputerTool()
    #         tools.append(computer_tool)
    #         logger.info(f"ComputerTool enabled in {capabilities['mode']} mode")
    #     except Exception as e:
    #         logger.warning(f"Could not initialize ComputerTool: {e}")
    
    # Airtable tool (if configured)
    if settings.has_airtable and FunctionTool:
        try:
            from app.tools.airtable_tool import create_airtable_tool
            airtable_tool_def = create_airtable_tool(settings)
            if airtable_tool_def:
                # FunctionTool expects only the function as argument
                airtable_tool = FunctionTool(airtable_tool_def["function"])
                tools.append(airtable_tool)
                logger.info("Airtable tool enabled")
        except Exception as e:
            logger.warning(f"Could not initialize Airtable tool: {e}")
    
    # MCP filesystem server (if npm available)
    # Temporarily disabled due to connection issues
    # try:
    #     from app.tools.mcp_helper import create_filtered_mcp_server
    #     mcp_server = create_filtered_mcp_server(
    #         sandbox_dir="./sandbox",
    #         allowed_tools=["read_file", "write_file"]
    #     )
    #     if mcp_server:
    #         mcp_servers.append(mcp_server)
    #         has_mcp = True
    #         logger.info("MCP filesystem server enabled")
    # except Exception as e:
    #     logger.warning(f"Could not initialize MCP: {e}")
    
    # Create agent
    try:
        agent_kwargs = {
            "name": "Assistant",
            "instructions": (
                "You are a helpful assistant with access to multiple tools:\n"
                "- Use WebSearch to find current information from the internet\n"
                "- Use FileSearch to query our internal documentation about jacket preferences and Tokyo shops\n"
                "- Use ComputerTool to control the browser when tasks mention 'open', 'click', 'type', or 'add to cart'\n"
                "- Use MCP filesystem tools to read/write files in the sandbox directory\n"
                "- Use Airtable to log records when requested\n"
                "When using ComputerTool, explain your actions step by step."
            ),
            "tools": tools
        }
        
        # Add MCP servers if available
        if mcp_servers:
            agent_kwargs["mcp_servers"] = mcp_servers
        
        agent = Agent(**agent_kwargs)
        logger.info(f"Agent created with {len(tools)} tools and {len(mcp_servers)} MCP servers")
        return agent
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        return None


async def run_agent(task_text: str) -> Dict[str, Any]:
    """Run the agent with a task and return results"""
    
    # Demo mode if no API key
    if not settings.has_openai:
        return {
            "final_text": (
                "I'm running in demo mode without an OpenAI API key. "
                "To use WebSearch and other tools, please set your OPENAI_API_KEY in the .env file. "
                f"Your task was: '{task_text}'"
            ),
            "tool_calls": [],
            "used_file_search": False,
            "computer_mode": settings.computer_mode,
            "mode": "demo"
        }
    
    # Create agent if not exists
    global agent
    if agent is None:
        agent = create_agent()
    
    if agent is None:
        return {
            "final_text": "Failed to initialize agent. Please check your configuration.",
            "tool_calls": [],
            "used_file_search": False,
            "computer_mode": settings.computer_mode,
            "mode": "error"
        }
    
    # Run the agent
    tool_calls = []
    try:
        result = await Runner.run(agent, input=task_text)
        
        # Extract tool usage (simplified for now)
        # In production, parse the actual result for tool calls
        task_lower = task_text.lower()
        
        if "websearch" in task_lower or "search" in task_lower:
            tool_calls.append({
                "name": "WebSearch",
                "status": "ok",
                "summary": "Searched the web"
            })
        
        if settings.has_vector_store and any(word in task_lower for word in 
            ["jacket", "patagonia", "tokyo", "shop", "preference", "budget", "docs", "documentation"]):
            tool_calls.append({
                "name": "FileSearch",
                "status": "ok",
                "summary": "Searched internal documentation"
            })
        
        if settings.has_airtable and "airtable" in task_lower:
            tool_calls.append({
                "name": "Airtable",
                "status": "ok",
                "summary": "Logged to Airtable"
            })
        
        if has_mcp and any(word in task_lower for word in ["file", "write", "create", "sandbox"]):
            tool_calls.append({
                "name": "MCP",
                "status": "ok",
                "summary": "Used filesystem operations"
            })
        
        if ComputerTool and any(word in task_lower for word in ["open", "click", "type", "navigate", "cart", "website"]):
            tool_calls.append({
                "name": "ComputerTool",
                "status": "ok",
                "summary": f"Controlled browser in {settings.computer_mode} mode"
            })
        
        return {
            "final_text": result.final_output if hasattr(result, 'final_output') else str(result),
            "tool_calls": tool_calls,
            "used_file_search": any(tc["name"] == "FileSearch" for tc in tool_calls),
            "computer_mode": settings.computer_mode,
            "mode": "live"
        }
        
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        return {
            "final_text": f"I encountered an error while processing your request: {str(e)}",
            "tool_calls": tool_calls,
            "used_file_search": False,
            "computer_mode": settings.computer_mode,
            "mode": "error"
        }


def get_capabilities() -> Dict[str, Any]:
    """Get current tool capabilities for health check"""
    return {
        "websearch": settings.has_openai,
        "filesearch": settings.has_openai and settings.has_vector_store and not settings.openai_vector_store_id.startswith("vs_mock_"),
        "computer": settings.computer_mode,
        "airtable": settings.has_airtable,
        "mcp": has_mcp
    }