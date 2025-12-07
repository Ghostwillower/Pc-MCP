"""Terminal service for safe command execution without admin privileges."""

import os
import shlex
from pathlib import Path
from typing import Dict, Any, List, Optional

from utils.command import run_command_async
from config import get_settings


class TerminalService:
    """Service for executing terminal commands safely without admin privileges."""
    
    # Commands that require admin/root privileges - these will be blocked
    BLOCKED_COMMANDS = {
        "sudo", "su", "doas", "pkexec",  # Privilege escalation
        "chmod", "chown", "chgrp",  # Permission changes (can be dangerous)
        "systemctl", "service",  # System service management
        "reboot", "shutdown", "poweroff", "halt",  # System power commands
        "mkfs", "fdisk", "parted", "gdisk",  # Disk partitioning
        "mount", "umount",  # Filesystem mounting
        "iptables", "ufw", "firewall-cmd",  # Firewall management
        "useradd", "usermod", "userdel", "groupadd", "groupmod", "groupdel",  # User management
        "passwd",  # Password changes
    }
    
    def __init__(self):
        self.settings = get_settings()
        # Define allowed base directories for command execution
        self.allowed_base_dirs = [
            self.settings.workspace_dir,
            Path.home(),  # User's home directory
            Path.cwd(),  # Current working directory
        ]
    
    def _is_path_allowed(self, path: Path) -> bool:
        """
        Check if a path is within allowed directories.
        
        Args:
            path: Path to check
            
        Returns:
            bool: True if path is allowed, False otherwise
        """
        try:
            resolved_path = path.resolve()
            # Check if path is within any allowed base directory
            for allowed_dir in self.allowed_base_dirs:
                try:
                    resolved_allowed = allowed_dir.resolve()
                    resolved_path.relative_to(resolved_allowed)
                    return True
                except ValueError:
                    continue
            return False
        except Exception:
            return False
    
    def _is_command_safe(self, command: str) -> tuple[bool, str]:
        """
        Check if a command is safe to execute (doesn't require admin).
        
        Args:
            command: Command string to check
            
        Returns:
            tuple: (is_safe, reason_if_not_safe)
        """
        # Parse command to get the base command
        try:
            parts = shlex.split(command)
            if not parts:
                return False, "Empty command"
            
            base_command = parts[0].split('/')[-1]  # Get command name without path
            
            # Check against blocked commands
            if base_command in self.BLOCKED_COMMANDS:
                return False, f"Command '{base_command}' requires admin privileges and is blocked"
            
            # Check for shell operators that could be used for privilege escalation
            dangerous_operators = ['|sudo', '&&sudo', ';sudo', '|su', '&&su', ';su']
            for op in dangerous_operators:
                if op in command:
                    return False, "Command contains privilege escalation attempt"
            
            return True, ""
            
        except Exception as e:
            return False, f"Failed to parse command: {str(e)}"
    
    async def execute_command(
        self,
        command: str,
        working_dir: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute a terminal command safely.
        
        Args:
            command: Command to execute
            working_dir: Working directory for command execution (default: workspace)
            timeout: Timeout in seconds (uses config default if None)
            
        Returns:
            dict: Contains command output and status
        """
        try:
            # Check if command is safe
            is_safe, reason = self._is_command_safe(command)
            if not is_safe:
                return {
                    "error": "Command blocked",
                    "details": reason,
                    "command": command
                }
            
            # Set working directory
            if working_dir:
                cwd = Path(working_dir).expanduser()
                if not self._is_path_allowed(cwd):
                    return {
                        "error": "Access denied",
                        "details": "Working directory is outside allowed directories"
                    }
                if not cwd.exists() or not cwd.is_dir():
                    return {
                        "error": "Invalid working directory",
                        "details": f"Directory does not exist: {working_dir}"
                    }
            else:
                cwd = self.settings.workspace_dir
            
            # Parse command into arguments
            try:
                args = shlex.split(command)
            except Exception as e:
                return {
                    "error": "Invalid command syntax",
                    "details": str(e)
                }
            
            # Execute command
            result = await run_command_async(args, timeout=timeout, cwd=cwd)
            
            return {
                "success": result.get("success", False),
                "command": command,
                "working_dir": str(cwd.resolve()),
                "exit_code": result.get("exit_code", -1),
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
            }
            
        except Exception as e:
            return {
                "error": "Failed to execute command",
                "details": str(e),
                "command": command
            }
    
    def get_current_directory(self) -> Dict[str, Any]:
        """
        Get the current working directory.
        
        Returns:
            dict: Contains current directory path
        """
        try:
            cwd = Path.cwd()
            return {
                "current_directory": str(cwd.resolve()),
                "is_allowed": self._is_path_allowed(cwd)
            }
        except Exception as e:
            return {
                "error": "Failed to get current directory",
                "details": str(e)
            }
    
    def get_environment_variables(self) -> Dict[str, Any]:
        """
        Get environment variables.
        
        Returns:
            dict: Contains environment variables
        """
        try:
            # Return only non-sensitive environment variables
            safe_vars = {}
            sensitive_patterns = ['KEY', 'SECRET', 'PASSWORD', 'TOKEN', 'CREDENTIAL']
            
            for key, value in os.environ.items():
                # Skip potentially sensitive variables
                is_sensitive = any(pattern in key.upper() for pattern in sensitive_patterns)
                if not is_sensitive:
                    safe_vars[key] = value
                else:
                    safe_vars[key] = "***REDACTED***"
            
            return {
                "environment_variables": safe_vars,
                "count": len(safe_vars)
            }
        except Exception as e:
            return {
                "error": "Failed to get environment variables",
                "details": str(e)
            }
