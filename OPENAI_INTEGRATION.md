# OpenAI MCP Connector Integration Guide

This guide explains how to use the CadSlicerPrinter MCP server with OpenAI's MCP connectors.

## Overview

The CadSlicerPrinter server is fully compatible with OpenAI's Model Context Protocol (MCP) connectors. It uses the `stdio` transport by default, which is the standard protocol for OpenAI integrations.

## Quick Start

### 1. Install the Server

```bash
# Clone the repository
git clone https://github.com/Ghostwillower/Pc-MCP.git
cd Pc-MCP

# Install dependencies
pip install -e .
```

### 2. Configure Environment Variables

```bash
export WORKSPACE_DIR="./workspace"
export OPENSCAD_BIN="/usr/bin/openscad"
export SLICER_BIN="/usr/bin/prusa-slicer"
export OCTOPRINT_URL="http://localhost:5000"
export OCTOPRINT_API_KEY="your-api-key-here"
```

### 3. Run the Server

For OpenAI integration, simply run:

```bash
cd src
python server.py
```

The server will start in `stdio` mode by default, which is compatible with OpenAI's MCP connectors.

## OpenAI Connector Configuration

### For Claude Desktop

Add the following to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "cadslicerprinter": {
      "command": "python",
      "args": ["/path/to/Pc-MCP/src/server.py"],
      "env": {
        "WORKSPACE_DIR": "./workspace",
        "OPENSCAD_BIN": "/usr/bin/openscad",
        "SLICER_BIN": "/usr/bin/prusa-slicer"
      }
    }
  }
}
```

### For Custom OpenAI Integrations

If you're building a custom integration using OpenAI's MCP SDK:

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configure the server
server_params = StdioServerParameters(
    command="python",
    args=["/path/to/Pc-MCP/src/server.py"],
    env={
        "WORKSPACE_DIR": "./workspace",
        "OPENSCAD_BIN": "/usr/bin/openscad",
        "SLICER_BIN": "/usr/bin/prusa-slicer"
    }
)

# Connect to the server
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        # Initialize the session
        await session.initialize()
        
        # List available tools
        tools = await session.list_tools()
        print(f"Available tools: {tools}")
        
        # Call a tool
        result = await session.call_tool(
            "cad_create_model",
            arguments={"description": "A simple box"}
        )
        print(f"Result: {result}")
```

## Available Tools

The server provides the following tools for 3D model workflows:

1. **cad_create_model** - Generate an initial parametric CAD file
2. **cad_modify_model** - Iteratively refine a model
3. **cad_render_preview** - Render a preview PNG
4. **cad_list_previews** - List available preview images
5. **slicer_slice_model** - Slice a model to G-code
6. **printer_status** - Get printer status via OctoPrint
7. **printer_upload_and_start** - Upload and start printing
8. **printer_send_gcode_line** - Send a G-code command
9. **workspace_list_models** - List all models in workspace

## Transport Modes

The server supports three transport modes:

### stdio (Default - OpenAI Compatible)
```bash
python server.py
# or explicitly:
python server.py --transport stdio
```

### HTTP (for web-based clients)
```bash
python server.py --transport streamable-http
# Server will be available at http://localhost:8000/mcp
```

### Server-Sent Events
```bash
python server.py --transport sse
```

## Environment Variables

You can configure the default transport using the `MCP_TRANSPORT` environment variable:

```bash
export MCP_TRANSPORT="stdio"  # Default
# or
export MCP_TRANSPORT="streamable-http"
# or
export MCP_TRANSPORT="sse"
```

## Workflow Example

Here's a typical workflow using the MCP tools:

1. **Create a model**
   ```
   Tool: cad_create_model
   Input: {"description": "A parametric phone stand"}
   Output: {"model_id": "abc123", "scad_path": "..."}
   ```

2. **Preview the design**
   ```
   Tool: cad_render_preview
   Input: {"model_id": "abc123", "view": "iso"}
   Output: {"png_path": "..."}
   ```

3. **Modify if needed**
   ```
   Tool: cad_modify_model
   Input: {"model_id": "abc123", "instruction": "Make it wider"}
   ```

4. **Slice for printing**
   ```
   Tool: slicer_slice_model
   Input: {"model_id": "abc123", "profile": "/path/to/profile.ini"}
   Output: {"gcode_path": "..."}
   ```

5. **Start printing**
   ```
   Tool: printer_upload_and_start
   Input: {"model_id": "abc123"}
   ```

## Troubleshooting

### Server not starting in stdio mode

Make sure all required dependencies are installed:
```bash
pip install -e .
```

### Tools returning errors

Check the environment variables are set correctly:
```bash
echo $OPENSCAD_BIN
echo $SLICER_BIN
echo $OCTOPRINT_API_KEY
```

### OpenAI connector can't find the server

Ensure the path to `server.py` is absolute in your connector configuration.

## Security Notes

- The server sanitizes model IDs to prevent directory traversal attacks
- No arbitrary shell command execution is exposed
- OctoPrint requires API key authentication
- All external tool calls are validated and sandboxed

## Support

For issues or questions:
- Check the main [README.md](README.md)
- Review [README_CADSLICERPRINTER.md](README_CADSLICERPRINTER.md) for detailed documentation
- Open an issue on GitHub
