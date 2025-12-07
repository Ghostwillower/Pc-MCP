"""Slicer-related MCP tools."""

from typing import Dict, Any, Optional
from mcp.server.fastmcp import FastMCP

from services import SlicerService


def register_slicer_tools(mcp: FastMCP, slicer_service: SlicerService) -> None:
    """Register slicer tools with the MCP server."""
    
    @mcp.tool()
    async def slicer_slice_model(
        model_id: str,
        profile: str,
        extra_args: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Slice a model using the configured slicer CLI to generate G-code.
        
        This is the critical step between design and printing. After finalizing
        your model design and previews, use this to generate the G-code that
        will be sent to the printer.
        
        Workflow:
        - After final cad_render_preview confirms design is ready
        - Use this to generate G-code with appropriate slicer profile
        - Then use printer_upload_and_start to begin printing
        
        Args:
            model_id: The model identifier
            profile: Path to slicer configuration/profile file
            extra_args: Optional dict of additional slicer arguments (e.g., {"layer-height": "0.2"})
            
        Returns:
            dict: Contains model_id, gcode_path, slicer_stdout, and slicer_stderr
            
        Example:
            >>> slicer_slice_model("abc123", "/path/to/profile.ini", {"layer-height": "0.2"})
            {
                "model_id": "abc123",
                "gcode_path": "/path/to/model.gcode",
                "slicer_stdout": "...",
                "slicer_stderr": ""
            }
        """
        return await slicer_service.slice_model(model_id, profile, extra_args)
