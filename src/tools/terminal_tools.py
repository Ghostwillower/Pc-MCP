"""Terminal-related MCP tools."""

from typing import Dict, Any, Optional
from mcp.server.fastmcp import FastMCP

from services import TerminalService


def register_terminal_tools(mcp: FastMCP, terminal_service: TerminalService) -> None:
    """Register terminal tools with the MCP server."""
    
    @mcp.tool()
    async def terminal_execute(
        command: str,
        working_dir: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute a terminal command safely without admin privileges.
        
        Use this to:
        - Run shell commands
        - Execute scripts
        - Build and test code
        - Interact with command-line tools
        
        Security:
        - Commands requiring admin/root are blocked (sudo, su, systemctl, etc.)
        - Working directory is restricted to allowed paths
        - Commands are validated before execution
        
        Blocked commands: sudo, su, chmod, chown, systemctl, reboot, shutdown, 
        mount, iptables, useradd, passwd, and other privileged operations.
        
        Args:
            command: Command to execute (shell syntax supported)
            working_dir: Working directory for command execution (default: workspace)
            timeout: Timeout in seconds (uses config default if None)
            
        Returns:
            dict: Contains command output, exit code, and status
            
        Example:
            >>> terminal_execute("ls -la")
            {
                "success": True,
                "command": "ls -la",
                "working_dir": "/path/to/workspace",
                "exit_code": 0,
                "stdout": "total 8\ndrwxr-xr-x  2 user user 4096 ...",
                "stderr": ""
            }
            
            >>> terminal_execute("python script.py", working_dir="~/projects")
            {
                "success": True,
                "command": "python script.py",
                "working_dir": "/home/user/projects",
                "exit_code": 0,
                "stdout": "Script output...",
                "stderr": ""
            }
        """
        return await terminal_service.execute_command(command, working_dir, timeout)
    
    @mcp.tool()
    def terminal_get_cwd() -> Dict[str, Any]:
        """
        Get the current working directory.
        
        Use this to:
        - Check current location
        - Verify working directory
        - Navigate filesystem
        
        Returns:
            dict: Contains current directory path and access status
            
        Example:
            >>> terminal_get_cwd()
            {
                "current_directory": "/home/user/workspace",
                "is_allowed": True
            }
        """
        return terminal_service.get_current_directory()
    
    @mcp.tool()
    def terminal_get_env() -> Dict[str, Any]:
        """
        Get environment variables.
        
        Use this to:
        - Check environment configuration
        - Debug environment issues
        - View system settings
        
        Security: Sensitive variables (containing KEY, SECRET, PASSWORD, TOKEN, 
        CREDENTIAL) are redacted.
        
        Returns:
            dict: Contains environment variables (sensitive ones redacted)
            
        Example:
            >>> terminal_get_env()
            {
                "environment_variables": {
                    "PATH": "/usr/bin:/bin",
                    "HOME": "/home/user",
                    "API_KEY": "***REDACTED***"
                },
                "count": 50
            }
        """
        return terminal_service.get_environment_variables()
