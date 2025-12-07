#!/usr/bin/env python3
"""
CadSlicerPrinter MCP Server - Redesigned for Maximum Backend Efficiency

A Python 3 MCP server that enables iterative 3D model design, preview, slicing,
and printing through ChatGPT and other MCP-compatible clients, or via the
included web control panel.

This redesigned version follows the OpenAI MCP framework with:
- Modular architecture for better maintainability
- Async operations for improved performance
- Connection pooling for external APIs
- Cached configuration and path lookups
- Clean separation of concerns (config, services, tools, web API)

Environment Variables:
- WORKSPACE_DIR: Directory for models, previews, and gcode (default: ./workspace)
- OPENSCAD_BIN: Path to OpenSCAD CLI executable
- SLICER_BIN: Path to slicer CLI executable
- OCTOPRINT_URL: OctoPrint URL (e.g., http://localhost:5000)
- OCTOPRINT_API_KEY: API key for OctoPrint authentication
- MCP_TRANSPORT: Transport protocol (stdio, sse, or streamable-http; default: stdio)

Command-line Arguments:
- --transport: Override MCP_TRANSPORT setting (stdio, sse, or streamable-http)
- --web: Enable web control panel (runs on port 8080)
- --port: Port for web control panel (default: 8080)
- --host: Host to bind web server to (default: 127.0.0.1)
"""

import sys
import logging
import argparse
import atexit
import signal
from pathlib import Path

# Ensure parent directory is in Python path for relative imports
_src_dir = Path(__file__).parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from mcp.server.fastmcp import FastMCP

# Import configuration
from config import get_settings

# Import services
from services import (
    CADService,
    SlicerService,
    PrinterService,
    WorkspaceService,
    FilesystemService,
    TerminalService,
)

# Import tool registration functions
from tools import (
    register_cad_tools,
    register_slicer_tools,
    register_printer_tools,
    register_workspace_tools,
    register_filesystem_tools,
    register_terminal_tools,
)

# Optional web server imports - only needed for --web mode
try:
    from starlette.applications import Starlette
    from starlette.routing import Route, Mount
    from starlette.responses import JSONResponse, FileResponse
    from starlette.staticfiles import StaticFiles
    import uvicorn
    WEB_DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    WEB_DEPENDENCIES_AVAILABLE = False
    _MISSING_WEB_DEP = str(e)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global service instances for cleanup
_printer_service = None


# ============================================================================
# LIFECYCLE MANAGEMENT
# ============================================================================

async def cleanup_services():
    """Clean up service resources on shutdown."""
    global _printer_service
    if _printer_service is not None:
        logger.info("Cleaning up printer service...")
        await _printer_service.close()


def register_cleanup_handlers():
    """Register cleanup handlers for graceful shutdown."""
    import asyncio
    
    def sync_cleanup():
        """Synchronous cleanup wrapper."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(cleanup_services())
            else:
                loop.run_until_complete(cleanup_services())
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    # Register cleanup on normal exit
    atexit.register(sync_cleanup)
    
    # Register cleanup on SIGTERM/SIGINT
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal, cleaning up...")
        sync_cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)


# ============================================================================
# SERVER INITIALIZATION
# ============================================================================

def create_mcp_server() -> FastMCP:
    """
    Create and configure the MCP server with all tools.
    
    Returns:
        Configured FastMCP instance
    """
    global _printer_service
    
    # Initialize FastMCP server
    mcp = FastMCP("CadSlicerPrinter", json_response=True)
    
    # Initialize services
    cad_service = CADService()
    slicer_service = SlicerService()
    _printer_service = PrinterService()  # Store for cleanup
    workspace_service = WorkspaceService()
    filesystem_service = FilesystemService()
    terminal_service = TerminalService()
    
    # Register all tools
    register_cad_tools(mcp, cad_service)
    register_slicer_tools(mcp, slicer_service)
    register_printer_tools(mcp, _printer_service)
    register_workspace_tools(mcp, workspace_service)
    register_filesystem_tools(mcp, filesystem_service)
    register_terminal_tools(mcp, terminal_service)
    
    return mcp


# ============================================================================
# STARTUP CHECKS
# ============================================================================

def startup_checks():
    """
    Perform startup checks and log configuration status.
    """
    settings = get_settings()
    
    logger.info("=" * 80)
    logger.info("CadSlicerPrinter MCP Server Starting (Redesigned)")
    logger.info("=" * 80)
    
    # Ensure workspace exists
    try:
        settings.ensure_workspace()
        logger.info(f"✓ Workspace directory: {settings.workspace_dir}")
    except Exception as e:
        logger.error(f"✗ Failed to create workspace directory: {e}")
    
    # Validate configuration
    validation_messages = settings.validate()
    if validation_messages:
        logger.warning("Configuration warnings:")
        for msg in validation_messages:
            logger.warning(f"  ⚠ {msg}")
    
    # Log configuration
    logger.info(f"✓ MCP Transport: {settings.mcp_transport}")
    if settings.openscad_bin:
        logger.info(f"✓ OpenSCAD binary: {settings.openscad_bin}")
    if settings.slicer_bin:
        logger.info(f"✓ Slicer binary: {settings.slicer_bin}")
    if settings.octoprint_url:
        logger.info(f"✓ OctoPrint URL: {settings.octoprint_url}")
    if settings.octoprint_api_key:
        logger.info(f"✓ OctoPrint API key: {settings.octoprint_api_key[:8]}...")
    
    logger.info("=" * 80)
    logger.info("Server ready. Available tools:")
    logger.info("  CAD Design:")
    logger.info("    - cad_create_model")
    logger.info("    - cad_get_code")
    logger.info("    - cad_update_parameters")
    logger.info("    - cad_modify_model")
    logger.info("    - cad_render_preview")
    logger.info("    - cad_list_previews")
    logger.info("  Slicing:")
    logger.info("    - slicer_slice_model")
    logger.info("  Printing:")
    logger.info("    - printer_status")
    logger.info("    - printer_upload_and_start")
    logger.info("    - printer_send_gcode_line")
    logger.info("  Workspace:")
    logger.info("    - workspace_list_models")
    logger.info("  Filesystem:")
    logger.info("    - filesystem_read_file")
    logger.info("    - filesystem_write_file")
    logger.info("    - filesystem_list_directory")
    logger.info("    - filesystem_create_directory")
    logger.info("    - filesystem_delete_path")
    logger.info("    - filesystem_get_info")
    logger.info("  Terminal:")
    logger.info("    - terminal_execute")
    logger.info("    - terminal_get_cwd")
    logger.info("    - terminal_get_env")
    logger.info("=" * 80)


def parse_arguments():
    """
    Parse command-line arguments for transport selection.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    settings = get_settings()
    
    parser = argparse.ArgumentParser(
        description="CadSlicerPrinter MCP Server - 3D model design, slicing, and printing"
    )
    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "sse", "streamable-http"],
        default=settings.mcp_transport,
        help="MCP transport protocol (default: stdio for OpenAI compatibility)"
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Enable web control panel (runs on port 8080)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=settings.web_port,
        help=f"Port for web control panel (default: {settings.web_port})"
    )
    parser.add_argument(
        "--host",
        type=str,
        default=settings.web_host,
        help=f"Host to bind web server to (default: {settings.web_host} for localhost only)"
    )
    return parser.parse_args()


# ============================================================================
# WEB API ENDPOINTS (for frontend control panel)
# ============================================================================

# Create services for web API
_cad_service = CADService()
_slicer_service = SlicerService()
_printer_service = PrinterService()
_workspace_service = WorkspaceService()


# Web API endpoints that wrap service methods
async def api_health(request):
    """Health check endpoint"""
    return JSONResponse({"status": "ok", "server": "CadSlicerPrinter"})


async def api_cad_create(request):
    """Create a new CAD model"""
    data = await request.json()
    result = _cad_service.create_model(description=data.get("description", ""))
    return JSONResponse(result)


async def api_cad_modify(request):
    """Modify an existing CAD model"""
    data = await request.json()
    result = _cad_service.add_modification_note(
        model_id=data.get("model_id", ""),
        instruction=data.get("instruction", "")
    )
    return JSONResponse(result)


async def api_cad_get_code(request):
    """Get the OpenSCAD code for a model"""
    data = await request.json()
    result = _cad_service.get_code(model_id=data.get("model_id", ""))
    return JSONResponse(result)


async def api_cad_update_parameters(request):
    """Update parameters in a CAD model"""
    data = await request.json()
    result = _cad_service.update_parameters(
        model_id=data.get("model_id", ""),
        parameters=data.get("parameters", {})
    )
    return JSONResponse(result)


async def api_cad_preview(request):
    """Render a preview of a CAD model"""
    data = await request.json()
    result = await _cad_service.render_preview(
        model_id=data.get("model_id", ""),
        view=data.get("view", "iso"),
        width=data.get("width", 800),
        height=data.get("height", 600)
    )
    return JSONResponse(result)


async def api_cad_list_previews(request):
    """List previews for a model"""
    data = await request.json()
    result = _cad_service.list_previews(model_id=data.get("model_id", ""))
    return JSONResponse(result)


async def api_slicer_slice(request):
    """Slice a model"""
    data = await request.json()
    result = await _slicer_service.slice_model(
        model_id=data.get("model_id", ""),
        profile=data.get("profile", ""),
        extra_args=data.get("extra_args")
    )
    return JSONResponse(result)


async def api_printer_status(_request):
    """Get printer status"""
    result = await _printer_service.get_status()
    return JSONResponse(result)


async def api_printer_upload_and_start(request):
    """Upload and start print"""
    data = await request.json()
    result = await _printer_service.upload_and_start(model_id=data.get("model_id", ""))
    return JSONResponse(result)


async def api_printer_send_gcode(request):
    """Send G-code command"""
    data = await request.json()
    result = await _printer_service.send_gcode(gcode=data.get("gcode", ""))
    return JSONResponse(result)


async def api_workspace_models(_request):
    """List all workspace models"""
    result = _workspace_service.list_models()
    return JSONResponse(result)


async def index(request):
    """Serve the main web interface"""
    static_dir = Path(__file__).parent / "static"
    return FileResponse(static_dir / "index.html")


# Create web application with both MCP and web API
def create_web_app():
    """Create a Starlette application with both MCP and web API endpoints"""
    static_dir = Path(__file__).parent / "static"
    
    routes = [
        Route("/", index),
        Route("/api/health", api_health, methods=["GET"]),
        Route("/api/cad/create", api_cad_create, methods=["POST"]),
        Route("/api/cad/modify", api_cad_modify, methods=["POST"]),
        Route("/api/cad/get-code", api_cad_get_code, methods=["POST"]),
        Route("/api/cad/update-parameters", api_cad_update_parameters, methods=["POST"]),
        Route("/api/cad/preview", api_cad_preview, methods=["POST"]),
        Route("/api/cad/list-previews", api_cad_list_previews, methods=["POST"]),
        Route("/api/slicer/slice", api_slicer_slice, methods=["POST"]),
        Route("/api/printer/status", api_printer_status, methods=["GET"]),
        Route("/api/printer/upload-and-start", api_printer_upload_and_start, methods=["POST"]),
        Route("/api/printer/send-gcode", api_printer_send_gcode, methods=["POST"]),
        Route("/api/workspace/models", api_workspace_models, methods=["GET"]),
        Mount("/static", StaticFiles(directory=str(static_dir)), name="static"),
    ]
    
    return Starlette(routes=routes)


def run_web_server(host="127.0.0.1", port=8080):
    """Run the web server with both MCP and web API"""
    if not WEB_DEPENDENCIES_AVAILABLE:
        logger.error("Web server dependencies not available!")
        logger.error(f"Missing dependency: {_MISSING_WEB_DEP}")
        logger.error("Install with: pip install uvicorn starlette")
        sys.exit(1)
    
    app = create_web_app()
    
    logger.info("=" * 80)
    logger.info(f"Web Control Panel available at: http://{host}:{port}")
    logger.info(f"MCP endpoints available at: http://{host}:{port}/api/...")
    if host == "0.0.0.0":
        logger.warning("⚠️  WARNING: Server is exposed to all network interfaces!")
        logger.warning("⚠️  Consider using --host 127.0.0.1 for localhost-only access")
    logger.info("=" * 80)
    
    uvicorn.run(app, host=host, port=port, log_level="info")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Register cleanup handlers
    register_cleanup_handlers()
    
    args = parse_arguments()
    startup_checks()
    
    # Check if we should run in web mode (with frontend)
    if args.web or args.transport == "streamable-http":
        logger.info("Starting server in web mode with control panel")
        run_web_server(host=args.host, port=args.port)
    else:
        # Log the transport being used
        logger.info(f"Starting MCP server with transport: {args.transport}")
        
        # Create and run the MCP server
        mcp = create_mcp_server()
        mcp.run(transport=args.transport)
