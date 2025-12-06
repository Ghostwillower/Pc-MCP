"""Command execution utilities with improved efficiency."""

import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import get_settings


def run_command_safe(
    args: List[str],
    timeout: Optional[int] = None,
    cwd: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Safely run a command and capture output (synchronous version).
    
    This is an internal helper function for calling external CAD and slicer binaries.
    It does NOT expose arbitrary command execution as a tool.
    
    Args:
        args: Command and arguments as a list
        timeout: Timeout in seconds (uses config default if None)
        cwd: Working directory for command execution
        
    Returns:
        dict: Contains stdout, stderr, exit_code, and optional error message
    """
    settings = get_settings()
    if timeout is None:
        timeout = settings.command_timeout
    
    max_output = settings.max_output_length
    
    try:
        result = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            cwd=cwd,
            text=True
        )
        
        return {
            "stdout": result.stdout[:max_output] if result.stdout else "",
            "stderr": result.stderr[:max_output] if result.stderr else "",
            "exit_code": result.returncode,
            "success": result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds",
            "exit_code": -1,
            "success": False,
            "error": "timeout"
        }
    except FileNotFoundError:
        return {
            "stdout": "",
            "stderr": f"Command not found: {args[0]}",
            "exit_code": -1,
            "success": False,
            "error": "command_not_found"
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1,
            "success": False,
            "error": str(e)
        }


async def run_command_async(
    args: List[str],
    timeout: Optional[int] = None,
    cwd: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Asynchronously run a command and capture output.
    
    This is more efficient for long-running commands as it doesn't block
    the event loop. Use this for rendering, slicing, and other time-intensive
    operations.
    
    Args:
        args: Command and arguments as a list
        timeout: Timeout in seconds (uses config default if None)
        cwd: Working directory for command execution
        
    Returns:
        dict: Contains stdout, stderr, exit_code, and optional error message
    """
    settings = get_settings()
    if timeout is None:
        timeout = settings.command_timeout
    
    max_output = settings.max_output_length
    
    try:
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
        )
        
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            stdout = stdout_bytes.decode('utf-8', errors='replace')[:max_output]
            stderr = stderr_bytes.decode('utf-8', errors='replace')[:max_output]
            
            return {
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": process.returncode,
                "success": process.returncode == 0
            }
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            return {
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "exit_code": -1,
                "success": False,
                "error": "timeout"
            }
    except FileNotFoundError:
        return {
            "stdout": "",
            "stderr": f"Command not found: {args[0]}",
            "exit_code": -1,
            "success": False,
            "error": "command_not_found"
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1,
            "success": False,
            "error": str(e)
        }
