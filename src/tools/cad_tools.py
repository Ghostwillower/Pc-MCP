"""CAD-related MCP tools."""

from typing import Dict, Any
from mcp.server.fastmcp import FastMCP

from services import CADService


def register_cad_tools(mcp: FastMCP, cad_service: CADService) -> None:
    """Register CAD tools with the MCP server."""
    
    @mcp.tool()
    def cad_create_model(description: str) -> Dict[str, Any]:
        """
        Generate an initial parametric CAD file from a natural-language description.
        
        This is the first step in the iterative design workflow:
        1. cad_create_model (create initial model)
        2. cad_render_preview (see what it looks like)
        3. cad_modify_model (refine based on preview)
        4. Repeat steps 2-3 as needed
        5. slicer_slice_model (prepare for printing)
        6. printer_upload_and_start (print the model)
        
        Args:
            description: Natural language description of the desired 3D model
            
        Returns:
            dict: Contains model_id and scad_path, or error information
            
        Example:
            >>> cad_create_model("A parametric phone stand with adjustable angle")
            {"model_id": "abc123", "scad_path": "/path/to/workspace/models/abc123/main.scad"}
        """
        return cad_service.create_model(description)
    
    @mcp.tool()
    def cad_get_code(model_id: str) -> Dict[str, Any]:
        """
        Retrieve the current OpenSCAD code for a model.
        
        This is essential for the iterative design workflow. Use this to:
        - See current parameter values before modifying
        - Understand the model structure
        - Check what parameters are available for modification
        - Review modification history
        
        The AI can use this to understand the current state of the model
        before making changes with cad_update_parameters.
        
        Args:
            model_id: The model identifier
            
        Returns:
            dict: Contains model_id, scad_path, and scad_code content
            
        Example:
            >>> cad_get_code("abc123")
            {
                "model_id": "abc123",
                "scad_path": "/path/to/main.scad",
                "scad_code": "// Model code here..."
            }
        """
        return cad_service.get_code(model_id)
    
    @mcp.tool()
    def cad_update_parameters(model_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update specific parameters in the OpenSCAD model.
        
        This is the key tool for iterative design refinement. After viewing a preview
        and identifying needed changes, use this to update parameter values directly.
        
        The iterative workflow:
        1. cad_render_preview() - See current model
        2. cad_get_code() - View current parameters (optional)
        3. cad_update_parameters() - Change specific parameters
        4. cad_render_preview() - See updated model
        5. Repeat steps 3-4 until satisfied
        
        This tool intelligently updates parameter assignments (e.g., "width = 50;")
        in the SCAD file while preserving the rest of the code structure.
        
        Args:
            model_id: The model identifier
            parameters: Dict of parameter names to new values (e.g., {"width": 80, "height": 50})
            
        Returns:
            dict: Contains model_id, scad_path, updated parameters list, and success status
            
        Example:
            >>> cad_update_parameters("abc123", {"width": 80, "height": 50, "wall_thickness": 3})
            {
                "model_id": "abc123",
                "scad_path": "...",
                "updated": ["width", "height", "wall_thickness"],
                "changes": {"width": "50 -> 80", "height": "30 -> 50", "wall_thickness": "2 -> 3"}
            }
        """
        return cad_service.update_parameters(model_id, parameters)
    
    @mcp.tool()
    def cad_modify_model(model_id: str, instruction: str) -> Dict[str, Any]:
        """
        Log a modification instruction for a model.
        
        This tool records modification intentions as comments in the SCAD file.
        For actual parameter updates, use cad_update_parameters() instead.
        
        Recommended workflow for iterative design:
        1. cad_render_preview() - See current state
        2. Compare preview with target design
        3. cad_get_code() - See current parameters
        4. cad_update_parameters() - Make specific changes
        5. cad_render_preview() - Verify changes
        6. Repeat 2-5 until design matches target
        
        Args:
            model_id: The model identifier
            instruction: Natural language instruction documenting the intended modification
            
        Returns:
            dict: Contains model_id, scad_path, and note about changes
            
        Example:
            >>> cad_modify_model("abc123", "Need to increase height for better stability")
            {"model_id": "abc123", "scad_path": "...", "note": "Added modification note"}
        """
        return cad_service.add_modification_note(model_id, instruction)
    
    @mcp.tool()
    async def cad_render_preview(
        model_id: str,
        view: str = "iso",
        width: int = 800,
        height: int = 600
    ) -> Dict[str, Any]:
        """
        Render a preview PNG of the model so you can see what it looks like.
        
        This is crucial in the iterative design workflow. After creating or modifying
        a model, use this to visualize the current state before proceeding with
        further modifications or slicing.
        
        Workflow integration:
        - After cad_create_model: render to see initial design
        - After cad_modify_model: render to verify changes
        - Before slicer_slice_model: render to confirm final design
        
        Args:
            model_id: The model identifier
            view: View angle (iso, top, bottom, left, right, front, back)
            width: Image width in pixels (default: 800)
            height: Image height in pixels (default: 600)
            
        Returns:
            dict: Contains model_id and png_path, or error information
            
        Example:
            >>> cad_render_preview("abc123", view="iso", width=1024, height=768)
            {"model_id": "abc123", "png_path": "/path/to/preview_12345.png"}
        """
        return await cad_service.render_preview(model_id, view, width, height)
    
    @mcp.tool()
    def cad_list_previews(model_id: str) -> Dict[str, Any]:
        """
        List available preview images for a model.
        
        Use this to see all generated previews and their modification times.
        Helpful for reviewing the design iteration history.
        
        Args:
            model_id: The model identifier
            
        Returns:
            dict: Contains model_id and list of previews with file and mtime
            
        Example:
            >>> cad_list_previews("abc123")
            {
                "model_id": "abc123",
                "previews": [
                    {"file": "preview_12345.png", "mtime": 1234567890.0},
                    {"file": "preview_12346.png", "mtime": 1234567900.0}
                ]
            }
        """
        return cad_service.list_previews(model_id)
