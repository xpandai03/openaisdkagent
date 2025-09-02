import logging
import subprocess
import shutil
from typing import Optional, Any, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


def check_npm_available() -> bool:
    """Check if npm is installed and available"""
    try:
        result = subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            logger.info(f"npm available: v{result.stdout.strip()}")
            return True
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    
    logger.warning("npm not found - MCP features will be disabled")
    return False


def create_mcp_filesystem_server(sandbox_dir: str = "./sandbox") -> Optional[Any]:
    """
    Create an MCP filesystem server if npm is available
    
    Args:
        sandbox_dir: Directory for filesystem operations
        
    Returns:
        MCP server instance or None if unavailable
    """
    if not check_npm_available():
        return None
    
    # Ensure sandbox directory exists
    Path(sandbox_dir).mkdir(exist_ok=True)
    
    try:
        # Try importing MCP support from agents SDK
        from agents.mcp import MCPServerStdio
        
        logger.info(f"Starting MCP filesystem server in {sandbox_dir}")
        
        # Create the MCP server with absolute path
        import os
        abs_sandbox = os.path.abspath(sandbox_dir)
        
        mcp_server = MCPServerStdio(
            params={
                "command": "npx",
                "args": [
                    "-y",
                    "@modelcontextprotocol/server-filesystem",
                    abs_sandbox
                ]
            }
        )
        
        logger.info(f"MCP filesystem server configured for {abs_sandbox}")
        return mcp_server
        
    except ImportError as e:
        logger.warning(f"MCP support not available in agents SDK: {e}")
        return None
    except Exception as e:
        logger.warning(f"Failed to start MCP server: {e}")
        return None


def create_filtered_mcp_server(sandbox_dir: str = "./sandbox", 
                              allowed_tools: list = None) -> Optional[Any]:
    """
    Create an MCP server with tool filtering
    
    Args:
        sandbox_dir: Directory for filesystem operations
        allowed_tools: List of allowed tool names (default: ["read_file", "write_file"])
        
    Returns:
        Filtered MCP server or None
    """
    if allowed_tools is None:
        allowed_tools = ["read_file", "write_file"]
    
    server = create_mcp_filesystem_server(sandbox_dir)
    if not server:
        return None
    
    try:
        # Try to add tool filtering
        from agents.mcp import create_static_tool_filter
        
        server.tool_filter = create_static_tool_filter(
            allowed_tool_names=allowed_tools
        )
        logger.info(f"MCP server filtered to: {allowed_tools}")
        
    except ImportError:
        logger.warning("Tool filtering not available - using unfiltered MCP")
    except Exception as e:
        logger.warning(f"Could not apply tool filter: {e}")
    
    return server


def test_mcp_server() -> Dict[str, Any]:
    """Test MCP server availability and configuration"""
    result = {
        "npm_available": check_npm_available(),
        "mcp_available": False,
        "test_status": "not_tested"
    }
    
    if not result["npm_available"]:
        result["test_status"] = "npm_missing"
        return result
    
    # Try to create a test server
    test_server = create_mcp_filesystem_server("./test_sandbox")
    if test_server:
        result["mcp_available"] = True
        result["test_status"] = "success"
        # Clean up test
        try:
            shutil.rmtree("./test_sandbox", ignore_errors=True)
        except:
            pass
    else:
        result["test_status"] = "mcp_creation_failed"
    
    return result