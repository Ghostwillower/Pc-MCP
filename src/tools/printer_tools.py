"""Printer-related MCP tools."""

from typing import Dict, Any
from mcp.server.fastmcp import FastMCP

from services import PrinterService


def register_printer_tools(mcp: FastMCP, printer_service: PrinterService) -> None:
    """Register printer tools with the MCP server."""
    
    @mcp.tool()
    async def printer_status() -> Dict[str, Any]:
        """
        Get the current status of the 3D printer via OctoPrint.
        
        Use this to check:
        - Current job progress
        - Printer state (operational, printing, paused, etc.)
        - Temperature information
        - Print time estimates
        
        Returns standard OctoPrint job and printer status.
        
        Returns:
            dict: Contains job and printer status information from OctoPrint
            
        Example:
            >>> printer_status()
            {
                "job": {"state": "Printing", "progress": {"completion": 45.2}},
                "printer": {"state": {"text": "Printing"}, "temperature": {...}}
            }
        """
        return await printer_service.get_status()
    
    @mcp.tool()
    async def printer_upload_and_start(model_id: str) -> Dict[str, Any]:
        """
        Upload G-code to OctoPrint and start the print job.
        
        This is the final step in the workflow. After slicing your model,
        use this to upload the G-code to your 3D printer and start printing.
        
        Workflow:
        1. Design complete and validated with previews
        2. G-code generated with slicer_slice_model
        3. Use this tool to upload and start printing
        4. Monitor with printer_status
        
        Args:
            model_id: The model identifier
            
        Returns:
            dict: Contains upload_result and start_result from OctoPrint
            
        Example:
            >>> printer_upload_and_start("abc123")
            {
                "model_id": "abc123",
                "upload_result": {...},
                "start_result": {...}
            }
        """
        return await printer_service.upload_and_start(model_id)
    
    @mcp.tool()
    async def printer_send_gcode_line(gcode: str) -> Dict[str, Any]:
        """
        Send a single G-code command to the printer.
        
        ⚠️  WARNING: This can move the printer or change temperatures!
        Use with caution. Only send G-code commands if you understand their effects.
        
        Common uses:
        - Home axes: G28
        - Set temperature: M104 S200 (hotend), M140 S60 (bed)
        - Move: G1 X10 Y10 Z5 F3000
        - Emergency stop: M112
        
        Args:
            gcode: The G-code command to send (e.g., "G28", "M104 S200")
            
        Returns:
            dict: Contains sent command and result from OctoPrint
            
        Example:
            >>> printer_send_gcode_line("G28")
            {"sent": "G28", "result": {...}}
        """
        return await printer_service.send_gcode(gcode)
