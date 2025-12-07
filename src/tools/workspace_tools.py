"""Workspace-related MCP tools."""

from typing import Dict, Any
from mcp.server.fastmcp import FastMCP

from services import WorkspaceService


def register_workspace_tools(mcp: FastMCP, workspace_service: WorkspaceService) -> None:
    """Register workspace tools with the MCP server."""
    
    @mcp.tool()
    def workspace_list_models() -> Dict[str, Any]:
        """
        List all models in the workspace.
        
        Use this to:
        - See all available models
        - Check which models have been sliced
        - Find models with previews
        - Manage your workspace
        
        Returns:
            dict: Contains list of models with their status
            
        Example:
            >>> workspace_list_models()
            {
                "models": [
                    {
                        "model_id": "abc123",
                        "scad_exists": True,
                        "gcode_exists": True,
                        "previews": 3
                    }
                ]
            }
        """
        return workspace_service.list_models()
