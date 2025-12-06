#!/usr/bin/env python3
"""
CadSlicerPrinter MCP Server

A Python 3 MCP server that enables iterative 3D model design, preview, slicing, and printing.
Provides tools for:
- CAD model creation and modification using OpenSCAD
- Preview rendering
- Model slicing with standard slicers (PrusaSlicer, Orca, CuraEngine)
- 3D printer control via OctoPrint

Environment Variables:
- WORKSPACE_DIR: Directory for models, previews, and gcode (default: ./workspace)
- OPENSCAD_BIN: Path to OpenSCAD CLI executable
- SLICER_BIN: Path to slicer CLI executable
- OCTOPRINT_URL: OctoPrint URL (e.g., http://localhost:5000)
- OCTOPRINT_API_KEY: API key for OctoPrint authentication
- MCP_TRANSPORT: Transport protocol (stdio, sse, or streamable-http; default: stdio)

Command-line Arguments:
- --transport: Override MCP_TRANSPORT setting (stdio, sse, or streamable-http)
"""

import os
import re
import sys
import logging
import subprocess
import uuid
import json
import time
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List

import requests
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("CadSlicerPrinter", json_response=True)

# Environment configuration
WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "./workspace")
OPENSCAD_BIN = os.getenv("OPENSCAD_BIN", "openscad")
SLICER_BIN = os.getenv("SLICER_BIN", "")
OCTOPRINT_URL = os.getenv("OCTOPRINT_URL", "http://localhost:5000")
OCTOPRINT_API_KEY = os.getenv("OCTOPRINT_API_KEY", "")

# Validate and set MCP transport
_VALID_TRANSPORTS = ["stdio", "sse", "streamable-http"]
_transport_env = os.getenv("MCP_TRANSPORT", "stdio")
if _transport_env not in _VALID_TRANSPORTS:
    logger.warning(f"Invalid MCP_TRANSPORT '{_transport_env}', using default 'stdio'")
    MCP_TRANSPORT = "stdio"
else:
    MCP_TRANSPORT = _transport_env

# Constants
MAX_OUTPUT_LENGTH = 10000  # Maximum length for stdout/stderr output


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def ensure_workspace() -> Path:
    """
    Ensure the workspace directory exists.
    
    Returns:
        Path: Absolute path to the workspace directory
    """
    workspace = Path(WORKSPACE_DIR).resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    models_dir = workspace / "models"
    models_dir.mkdir(exist_ok=True)
    return workspace


def sanitize_model_id(model_id: str) -> str:
    """
    Sanitize model_id to prevent directory traversal attacks.
    
    Args:
        model_id: The model identifier
        
    Returns:
        str: Sanitized model_id
        
    Raises:
        ValueError: If model_id contains invalid characters
    """
    # Only allow alphanumeric, hyphens, and underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', model_id):
        raise ValueError(f"Invalid model_id: {model_id}. Only alphanumeric, hyphens, and underscores allowed.")
    return model_id


def model_dir(model_id: str) -> Path:
    """
    Get the directory path for a specific model.
    
    Args:
        model_id: The model identifier
        
    Returns:
        Path: Absolute path to the model directory
        
    Raises:
        ValueError: If model_id is invalid
    """
    sanitized_id = sanitize_model_id(model_id)
    workspace = ensure_workspace()
    return workspace / "models" / sanitized_id


def run_command_safe(args: List[str], timeout: int = 60, cwd: Optional[Path] = None) -> Dict[str, Any]:
    """
    Safely run a command and capture output.
    
    This is an internal helper function for calling external CAD and slicer binaries.
    It does NOT expose arbitrary command execution as a tool.
    
    Args:
        args: Command and arguments as a list
        timeout: Timeout in seconds
        cwd: Working directory for command execution
        
    Returns:
        dict: Contains stdout, stderr, exit_code, and optional error message
    """
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
            "stdout": result.stdout[:MAX_OUTPUT_LENGTH] if result.stdout else "",
            "stderr": result.stderr[:MAX_OUTPUT_LENGTH] if result.stderr else "",
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


def octo_get(path: str) -> Dict[str, Any]:
    """
    Make a GET request to OctoPrint API.
    
    Args:
        path: API path (e.g., "/api/job")
        
    Returns:
        dict: Response data or error information
    """
    if not OCTOPRINT_API_KEY:
        return {"error": "OCTOPRINT_API_KEY not configured"}
    
    try:
        url = f"{OCTOPRINT_URL.rstrip('/')}{path}"
        headers = {"X-Api-Key": OCTOPRINT_API_KEY}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 204:
            return {"status": 204}
        
        if response.status_code in (200, 201):
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"status": response.status_code, "body": response.text}
        
        return {
            "error": f"HTTP {response.status_code}",
            "status": response.status_code,
            "body": response.text[:500]
        }
    except requests.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}


def octo_post(path: str, payload: Optional[Dict[str, Any]] = None, files: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Make a POST request to OctoPrint API.
    
    Args:
        path: API path
        payload: JSON payload (optional)
        files: Files to upload (optional)
        
    Returns:
        dict: Response data or error information
    """
    if not OCTOPRINT_API_KEY:
        return {"error": "OCTOPRINT_API_KEY not configured"}
    
    try:
        url = f"{OCTOPRINT_URL.rstrip('/')}{path}"
        headers = {"X-Api-Key": OCTOPRINT_API_KEY}
        
        if files:
            # Don't set Content-Type for multipart/form-data
            response = requests.post(url, headers=headers, files=files, data=payload, timeout=30)
        else:
            headers["Content-Type"] = "application/json"
            response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 204:
            return {"status": 204}
        
        if response.status_code in (200, 201):
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"status": response.status_code, "body": response.text}
        
        return {
            "error": f"HTTP {response.status_code}",
            "status": response.status_code,
            "body": response.text[:500]
        }
    except requests.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}


# ============================================================================
# MCP TOOLS
# ============================================================================

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
    try:
        # Generate unique model ID
        model_id = str(uuid.uuid4())[:8]
        
        # Create model directory
        mdir = model_dir(model_id)
        mdir.mkdir(parents=True, exist_ok=True)
        
        # Generate OpenSCAD template
        # This is a simple parametric template that can be hand-edited
        scad_content = f"""// {description}
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
        
        scad_path = mdir / "main.scad"
        scad_path.write_text(scad_content)
        
        logger.info(f"Created model {model_id} at {scad_path}")
        
        return {
            "model_id": model_id,
            "scad_path": str(scad_path.resolve()),
        }
        
    except Exception as e:
        logger.error(f"Error creating model: {e}", exc_info=True)
        return {
            "error": "Failed to create model",
            "details": str(e)
        }


@mcp.tool()
def cad_modify_model(model_id: str, instruction: str) -> Dict[str, Any]:
    """
    Iteratively refine a model using text instructions.
    
    Note: This is a placeholder implementation that logs modification instructions
    as comments in the SCAD file. In a production system, you would integrate an
    LLM or code transformation tool to actually modify the parametric code based
    on the instruction. For now, ChatGPT can drive modifications by providing
    specific parameter changes or code edits through multiple calls.
    
    This tool allows you to track modification history and provides a foundation
    for more sophisticated code transformation in the future.
    
    Workflow:
    - After cad_render_preview shows the current state
    - Use this to document desired changes
    - Then manually edit the SCAD file or use another tool to apply changes
    - Render another preview to see the changes
    
    Args:
        model_id: The model identifier
        instruction: Natural language instruction for modification
        
    Returns:
        dict: Contains model_id, scad_path, and note about changes
        
    Example:
        >>> cad_modify_model("abc123", "Increase the height to 50mm")
        {"model_id": "abc123", "scad_path": "...", "note": "Modified model"}
    """
    try:
        sanitized_id = sanitize_model_id(model_id)
        mdir = model_dir(sanitized_id)
        scad_path = mdir / "main.scad"
        
        if not scad_path.exists():
            return {
                "error": "Model not found",
                "details": f"No main.scad found for model {model_id}"
            }
        
        # Read existing content
        existing_content = scad_path.read_text()
        
        # Add modification instruction as a comment
        # In a real implementation, you might use an LLM to actually modify the code
        # For now, we'll append a modification note
        modification_note = f"\n// MODIFICATION: {instruction}\n// Applied at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        # Simple modification: append the instruction as a comment
        # ChatGPT can drive more sophisticated modifications through multiple calls
        modified_content = existing_content + modification_note
        
        scad_path.write_text(modified_content)
        
        logger.info(f"Modified model {model_id}: {instruction}")
        
        return {
            "model_id": model_id,
            "scad_path": str(scad_path.resolve()),
            "note": f"Added modification instruction: {instruction}"
        }
        
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error modifying model: {e}", exc_info=True)
        return {
            "error": "Failed to modify model",
            "details": str(e)
        }


@mcp.tool()
def cad_render_preview(
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
    try:
        if not OPENSCAD_BIN:
            return {
                "error": "OPENSCAD_BIN not configured",
                "details": "Set the OPENSCAD_BIN environment variable to the OpenSCAD executable path"
            }
        
        sanitized_id = sanitize_model_id(model_id)
        mdir = model_dir(sanitized_id)
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
            OPENSCAD_BIN,
            "-o", str(png_path),
            f"--imgsize={width},{height}",
            "--render",
            str(scad_path)
        ]
        
        # Add view parameter if supported
        # Note: OpenSCAD camera positioning varies by version
        # This is a simplified approach
        if view != "iso":
            # You could add camera parameters here
            # For now, we'll just note the view in logs
            logger.info(f"Requested view: {view} (using default rendering)")
        
        # Execute OpenSCAD
        result = run_command_safe(cmd, timeout=120, cwd=mdir)
        
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
        
        logger.info(f"Rendered preview for model {model_id}: {png_path}")
        
        return {
            "model_id": model_id,
            "png_path": str(png_path.resolve())
        }
        
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error rendering preview: {e}", exc_info=True)
        return {
            "error": "Failed to render preview",
            "details": str(e)
        }


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
    try:
        sanitized_id = sanitize_model_id(model_id)
        mdir = model_dir(sanitized_id)
        
        if not mdir.exists():
            return {
                "error": "Model not found",
                "details": f"Model directory does not exist for {model_id}"
            }
        
        # Find all preview PNG files
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
        logger.error(f"Error listing previews: {e}", exc_info=True)
        return {
            "error": "Failed to list previews",
            "details": str(e)
        }


@mcp.tool()
def slicer_slice_model(
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
    try:
        if not SLICER_BIN:
            return {
                "error": "SLICER_BIN not configured",
                "details": "Set the SLICER_BIN environment variable to the slicer executable path"
            }
        
        if not OPENSCAD_BIN:
            return {
                "error": "OPENSCAD_BIN not configured",
                "details": "OpenSCAD is required to generate STL from SCAD file"
            }
        
        sanitized_id = sanitize_model_id(model_id)
        mdir = model_dir(sanitized_id)
        scad_path = mdir / "main.scad"
        
        if not scad_path.exists():
            return {
                "error": "Model not found",
                "details": f"No main.scad found for model {model_id}"
            }
        
        # Step 1: Generate STL from OpenSCAD
        stl_path = mdir / "model.stl"
        stl_cmd = [
            OPENSCAD_BIN,
            "-o", str(stl_path),
            str(scad_path)
        ]
        
        logger.info(f"Generating STL for model {model_id}")
        stl_result = run_command_safe(stl_cmd, timeout=180, cwd=mdir)
        
        if not stl_result["success"]:
            return {
                "error": "STL generation failed",
                "details": stl_result["stderr"],
                "stdout": stl_result["stdout"]
            }
        
        if not stl_path.exists():
            return {
                "error": "STL file not generated",
                "details": "OpenSCAD completed but no STL was created"
            }
        
        # Step 2: Slice STL to G-code
        gcode_path = mdir / "model.gcode"
        slice_cmd = [
            SLICER_BIN,
            "--load", profile,
            "--output", str(gcode_path),
            str(stl_path)
        ]
        
        # Add extra arguments if provided
        if extra_args:
            for key, value in extra_args.items():
                slice_cmd.extend([f"--{key}", value])
        
        logger.info(f"Slicing model {model_id} with profile {profile}")
        slice_result = run_command_safe(slice_cmd, timeout=300, cwd=mdir)
        
        if not slice_result["success"]:
            return {
                "error": "Slicing failed",
                "details": slice_result["stderr"],
                "stdout": slice_result["stdout"]
            }
        
        if not gcode_path.exists():
            return {
                "error": "G-code not generated",
                "details": "Slicer completed but no G-code was created"
            }
        
        logger.info(f"Sliced model {model_id}: {gcode_path}")
        
        return {
            "model_id": model_id,
            "gcode_path": str(gcode_path.resolve()),
            "slicer_stdout": slice_result["stdout"],
            "slicer_stderr": slice_result["stderr"]
        }
        
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error slicing model: {e}", exc_info=True)
        return {
            "error": "Failed to slice model",
            "details": str(e)
        }


@mcp.tool()
def printer_status() -> Dict[str, Any]:
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
    try:
        if not OCTOPRINT_API_KEY:
            return {
                "error": "OCTOPRINT_API_KEY not configured",
                "details": "Set the OCTOPRINT_API_KEY environment variable"
            }
        
        job_status = octo_get("/api/job")
        printer_status_data = octo_get("/api/printer")
        
        return {
            "job": job_status,
            "printer": printer_status_data
        }
        
    except Exception as e:
        logger.error(f"Error getting printer status: {e}", exc_info=True)
        return {
            "error": "Failed to get printer status",
            "details": str(e)
        }


@mcp.tool()
def printer_upload_and_start(model_id: str) -> Dict[str, Any]:
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
    try:
        if not OCTOPRINT_API_KEY:
            return {
                "error": "OCTOPRINT_API_KEY not configured",
                "details": "Set the OCTOPRINT_API_KEY environment variable"
            }
        
        sanitized_id = sanitize_model_id(model_id)
        mdir = model_dir(sanitized_id)
        gcode_path = mdir / "model.gcode"
        
        if not gcode_path.exists():
            return {
                "error": "G-code not found",
                "details": f"No model.gcode found for model {model_id}. Run slicer_slice_model first."
            }
        
        # Upload file to OctoPrint
        filename = f"{model_id}_model.gcode"
        
        with open(gcode_path, 'rb') as f:
            files = {'file': (filename, f, 'application/octet-stream')}
            upload_result = octo_post("/api/files/local", files=files)
        
        if "error" in upload_result:
            return {
                "model_id": model_id,
                "upload_result": upload_result,
                "error": "Upload failed"
            }
        
        # Start the print job
        start_payload = {
            "command": "select",
            "print": True
        }
        
        # The file path in OctoPrint
        file_path = f"local/{filename}"
        start_result = octo_post(f"/api/files/{file_path}", payload=start_payload)
        
        logger.info(f"Uploaded and started print for model {model_id}")
        
        return {
            "model_id": model_id,
            "upload_result": upload_result,
            "start_result": start_result
        }
        
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error uploading and starting print: {e}", exc_info=True)
        return {
            "error": "Failed to upload and start print",
            "details": str(e)
        }


@mcp.tool()
def printer_send_gcode_line(gcode: str) -> Dict[str, Any]:
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
    try:
        if not OCTOPRINT_API_KEY:
            return {
                "error": "OCTOPRINT_API_KEY not configured",
                "details": "Set the OCTOPRINT_API_KEY environment variable"
            }
        
        result = octo_post("/api/printer/command", payload={"commands": [gcode]})
        
        logger.warning(f"Sent G-code command: {gcode}")
        
        return {
            "sent": gcode,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error sending G-code: {e}", exc_info=True)
        return {
            "error": "Failed to send G-code",
            "details": str(e)
        }


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
    try:
        workspace = ensure_workspace()
        models_base = workspace / "models"
        
        if not models_base.exists():
            return {"models": []}
        
        models = []
        for model_path in sorted(models_base.iterdir()):
            if not model_path.is_dir():
                continue
            
            model_id = model_path.name
            
            # Check for main.scad
            scad_exists = (model_path / "main.scad").exists()
            
            # Check for gcode
            gcode_exists = (model_path / "model.gcode").exists()
            
            # Count previews
            preview_count = len(list(model_path.glob("preview_*.png")))
            
            models.append({
                "model_id": model_id,
                "scad_exists": scad_exists,
                "gcode_exists": gcode_exists,
                "previews": preview_count
            })
        
        return {"models": models}
        
    except Exception as e:
        logger.error(f"Error listing models: {e}", exc_info=True)
        return {
            "error": "Failed to list models",
            "details": str(e)
        }


# ============================================================================
# STARTUP LOGIC
# ============================================================================

def startup_checks():
    """
    Perform startup checks and log configuration status.
    """
    logger.info("=" * 80)
    logger.info("CadSlicerPrinter MCP Server Starting")
    logger.info("=" * 80)
    
    # Ensure workspace exists
    try:
        workspace = ensure_workspace()
        logger.info(f"✓ Workspace directory: {workspace}")
    except Exception as e:
        logger.error(f"✗ Failed to create workspace directory: {e}")
    
    # Check OpenSCAD
    if OPENSCAD_BIN:
        logger.info(f"✓ OpenSCAD binary: {OPENSCAD_BIN}")
    else:
        logger.warning("⚠ OPENSCAD_BIN not configured - CAD features will not work")
    
    # Check Slicer
    if SLICER_BIN:
        logger.info(f"✓ Slicer binary: {SLICER_BIN}")
    else:
        logger.warning("⚠ SLICER_BIN not configured - slicing features will not work")
    
    # Check OctoPrint
    if OCTOPRINT_URL:
        logger.info(f"✓ OctoPrint URL: {OCTOPRINT_URL}")
    else:
        logger.warning("⚠ OCTOPRINT_URL not configured")
    
    if OCTOPRINT_API_KEY:
        logger.info(f"✓ OctoPrint API key: {OCTOPRINT_API_KEY[:8]}...")
    else:
        logger.warning("⚠ OCTOPRINT_API_KEY not configured - printer features will not work")
    
    logger.info("=" * 80)
    logger.info("Server ready. Available tools:")
    logger.info("  - cad_create_model")
    logger.info("  - cad_modify_model")
    logger.info("  - cad_render_preview")
    logger.info("  - cad_list_previews")
    logger.info("  - slicer_slice_model")
    logger.info("  - printer_status")
    logger.info("  - printer_upload_and_start")
    logger.info("  - printer_send_gcode_line")
    logger.info("  - workspace_list_models")
    logger.info("=" * 80)


def parse_arguments():
    """
    Parse command-line arguments for transport selection.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="CadSlicerPrinter MCP Server - 3D model design, slicing, and printing"
    )
    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "sse", "streamable-http"],
        default=MCP_TRANSPORT,
        help="MCP transport protocol (default: stdio for OpenAI compatibility)"
    )
    return parser.parse_args()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    args = parse_arguments()
    startup_checks()
    
    # Log the transport being used
    logger.info(f"Starting MCP server with transport: {args.transport}")
    
    # Run the server with the selected transport
    mcp.run(transport=args.transport)
