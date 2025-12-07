"""CAD service for model creation and manipulation."""

import time
import uuid
import re
from pathlib import Path
from typing import Dict, Any

from config import get_settings
from utils import get_model_dir, run_command_async


class CADService:
    """Service for CAD model operations using OpenSCAD."""
    
    def __init__(self):
        self.settings = get_settings()
    
    def create_model(self, description: str) -> Dict[str, Any]:
        """
        Generate an initial parametric CAD file from a description.
        
        Args:
            description: Natural language description of the desired 3D model
            
        Returns:
            dict: Contains model_id and scad_path, or error information
        """
        try:
            # Generate unique model ID
            model_id = str(uuid.uuid4())[:8]
            
            # Create model directory
            mdir = get_model_dir(model_id)
            mdir.mkdir(parents=True, exist_ok=True)
            
            # Generate OpenSCAD template
            scad_content = self._generate_template(description)
            
            scad_path = mdir / "main.scad"
            scad_path.write_text(scad_content)
            
            return {
                "model_id": model_id,
                "scad_path": str(scad_path.resolve()),
            }
            
        except Exception as e:
            return {
                "error": "Failed to create model",
                "details": str(e)
            }
    
    def get_code(self, model_id: str) -> Dict[str, Any]:
        """
        Retrieve the current OpenSCAD code for a model.
        
        Args:
            model_id: The model identifier
            
        Returns:
            dict: Contains model_id, scad_path, and scad_code content
        """
        try:
            mdir = get_model_dir(model_id)
            scad_path = mdir / "main.scad"
            
            if not scad_path.exists():
                return {
                    "error": "Model not found",
                    "details": f"No main.scad found for model {model_id}"
                }
            
            scad_code = scad_path.read_text()
            
            return {
                "model_id": model_id,
                "scad_path": str(scad_path.resolve()),
                "scad_code": scad_code
            }
            
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            return {
                "error": "Failed to retrieve code",
                "details": str(e)
            }
    
    def update_parameters(self, model_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update specific parameters in the OpenSCAD model.
        
        Args:
            model_id: The model identifier
            parameters: Dict of parameter names to new values
            
        Returns:
            dict: Contains model_id, scad_path, updated parameters list, and success status
        """
        try:
            mdir = get_model_dir(model_id)
            scad_path = mdir / "main.scad"
            
            if not scad_path.exists():
                return {
                    "error": "Model not found",
                    "details": f"No main.scad found for model {model_id}"
                }
            
            # Read existing content
            content = scad_path.read_text()
            
            updated = []
            changes = {}
            not_found = []
            
            # Update each parameter
            for param_name, param_value in parameters.items():
                pattern = re.compile(
                    rf'^(\s*)({re.escape(param_name)})\s*=\s*([^;]+);',
                    re.MULTILINE
                )
                
                match = pattern.search(content)
                if match:
                    old_value = match.group(3).strip()
                    new_value = self._format_value(param_value)
                    new_line = f'{match.group(1)}{param_name} = {new_value};'
                    content = pattern.sub(new_line, content, count=1)
                    
                    updated.append(param_name)
                    changes[param_name] = f"{old_value} -> {new_value}"
                else:
                    not_found.append(param_name)
            
            # Write updated content back to file
            if updated:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                mod_log = f"\n// Updated parameters at {timestamp}: {', '.join(updated)}\n"
                content = content + mod_log
                scad_path.write_text(content)
                
                result = {
                    "model_id": model_id,
                    "scad_path": str(scad_path.resolve()),
                    "updated": updated,
                    "changes": changes
                }
                
                if not_found:
                    result["not_found"] = not_found
                    result["warning"] = f"Parameters not found: {', '.join(not_found)}"
                
                return result
            else:
                return {
                    "error": "No parameters updated",
                    "details": "None of the specified parameters were found in the model",
                    "not_found": not_found,
                    "hint": "Use cad_get_code() to see available parameters"
                }
            
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            return {
                "error": "Failed to update parameters",
                "details": str(e)
            }
    
    def add_modification_note(self, model_id: str, instruction: str) -> Dict[str, Any]:
        """
        Add a modification note to the model.
        
        Args:
            model_id: The model identifier
            instruction: Natural language instruction documenting the intended modification
            
        Returns:
            dict: Contains model_id, scad_path, and note about changes
        """
        try:
            mdir = get_model_dir(model_id)
            scad_path = mdir / "main.scad"
            
            if not scad_path.exists():
                return {
                    "error": "Model not found",
                    "details": f"No main.scad found for model {model_id}"
                }
            
            existing_content = scad_path.read_text()
            modification_note = (
                f"\n// NOTE: {instruction}\n"
                f"// Logged at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            
            modified_content = existing_content + modification_note
            scad_path.write_text(modified_content)
            
            return {
                "model_id": model_id,
                "scad_path": str(scad_path.resolve()),
                "note": f"Added modification note: {instruction}",
                "hint": "Use cad_update_parameters() to make actual parameter changes"
            }
            
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            return {
                "error": "Failed to modify model",
                "details": str(e)
            }
    
    async def render_preview(
        self,
        model_id: str,
        view: str = "iso",
        width: int = 800,
        height: int = 600
    ) -> Dict[str, Any]:
        """
        Render a preview PNG of the model (async for efficiency).
        
        Args:
            model_id: The model identifier
            view: View angle (iso, top, bottom, left, right, front, back)
            width: Image width in pixels
            height: Image height in pixels
            
        Returns:
            dict: Contains model_id and png_path, or error information
        """
        try:
            if not self.settings.openscad_bin:
                return {
                    "error": "OPENSCAD_BIN not configured",
                    "details": "Set the OPENSCAD_BIN environment variable"
                }
            
            mdir = get_model_dir(model_id)
            scad_path = mdir / "main.scad"
            
            if not scad_path.exists():
                return {
                    "error": "Model not found",
                    "details": f"No main.scad found for model {model_id}"
                }
            
            # Generate unique preview filename
            timestamp = int(time.time() * 1000)
            png_filename = f"preview_{timestamp}.png"
            png_path = mdir / png_filename
            
            # Build OpenSCAD command
            cmd = [
                self.settings.openscad_bin,
                "-o", str(png_path),
                f"--imgsize={width},{height}",
                "--render",
                str(scad_path)
            ]
            
            # Execute OpenSCAD asynchronously
            result = await run_command_async(cmd, timeout=120, cwd=mdir)
            
            if not result["success"]:
                return {
                    "error": "OpenSCAD rendering failed",
                    "details": result["stderr"],
                    "stdout": result["stdout"]
                }
            
            if not png_path.exists():
                return {
                    "error": "Preview file not generated",
                    "details": "OpenSCAD completed but no PNG was created"
                }
            
            return {
                "model_id": model_id,
                "png_path": str(png_path.resolve())
            }
            
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            return {
                "error": "Failed to render preview",
                "details": str(e)
            }
    
    def list_previews(self, model_id: str) -> Dict[str, Any]:
        """
        List available preview images for a model.
        
        Args:
            model_id: The model identifier
            
        Returns:
            dict: Contains model_id and list of previews with file and mtime
        """
        try:
            mdir = get_model_dir(model_id)
            
            if not mdir.exists():
                return {
                    "error": "Model not found",
                    "details": f"Model directory does not exist for {model_id}"
                }
            
            previews = []
            for png_file in sorted(mdir.glob("preview_*.png")):
                previews.append({
                    "file": png_file.name,
                    "mtime": png_file.stat().st_mtime
                })
            
            return {
                "model_id": model_id,
                "previews": previews
            }
            
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            return {
                "error": "Failed to list previews",
                "details": str(e)
            }
    
    @staticmethod
    def _format_value(value: Any) -> str:
        """Format a Python value for OpenSCAD."""
        if isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, str):
            if not (value.startswith('"') and value.endswith('"')):
                return f'"{value}"'
            return value
        else:
            return str(value)
    
    @staticmethod
    def _generate_template(description: str) -> str:
        """Generate an OpenSCAD template."""
        return f"""// {description}
// Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

// ============================================================================
// PARAMETERS - Modify these to customize the model
// ============================================================================

// Basic dimensions
width = 50;
depth = 50;
height = 30;

// Feature toggles
enable_base = true;
enable_holes = false;

// Advanced parameters
wall_thickness = 2;
corner_radius = 3;

// ============================================================================
// MODEL DEFINITION
// ============================================================================

module main_body() {{
    // Create the main body with rounded corners
    hull() {{
        for (x = [corner_radius, width - corner_radius]) {{
            for (y = [corner_radius, depth - corner_radius]) {{
                translate([x, y, 0])
                    cylinder(r = corner_radius, h = height, $fn = 30);
            }}
        }}
    }}
}}

module holes() {{
    // Example: mounting holes in corners
    hole_diameter = 3;
    hole_inset = 8;
    
    for (x = [hole_inset, width - hole_inset]) {{
        for (y = [hole_inset, depth - hole_inset]) {{
            translate([x, y, -1])
                cylinder(d = hole_diameter, h = height + 2, $fn = 20);
        }}
    }}
}}

// ============================================================================
// FINAL MODEL ASSEMBLY
// ============================================================================

difference() {{
    main_body();
    
    // Optionally add holes
    if (enable_holes) {{
        holes();
    }}
}}

// Add a base plate if enabled
if (enable_base) {{
    translate([0, 0, -2])
        cube([width, depth, 2]);
}}
"""
