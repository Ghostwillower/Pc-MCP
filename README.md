# Pc-MCP
MCP servers for my PC

## CadSlicerPrinter MCP Server

A Python 3 MCP server that enables iterative 3D model design, preview, slicing, and printing through ChatGPT and other MCP-compatible clients, or via the included web control panel.

### Features

- **CAD Model Design**: Create and modify parametric OpenSCAD models using natural language
- **Preview Rendering**: Visualize models at any stage of the design process
- **Model Slicing**: Generate G-code using industry-standard slicers
- **3D Printer Control**: Upload and start print jobs via OctoPrint
- **Web Control Panel**: Minimalist web interface for controlling all functions
- **Auto-Start Support**: Run as a system service on boot without GUI
- **OpenAI Compatible**: Uses stdio transport for seamless integration with OpenAI's MCP connectors

### Quick Start

See [README_CADSLICERPRINTER.md](README_CADSLICERPRINTER.md) for detailed documentation.

```bash
# Install dependencies
pip install -e .

# Configure environment
export WORKSPACE_DIR="./workspace"
export OPENSCAD_BIN="/usr/bin/openscad"
export SLICER_BIN="/usr/bin/prusa-slicer"
export OCTOPRINT_URL="http://localhost:5000"
export OCTOPRINT_API_KEY="your-api-key"

# Run the server (stdio mode - default, OpenAI compatible)
cd src
python server.py

# Or run with web control panel
python server.py --web

# Or run with HTTP transport for web-based clients
python server.py --transport streamable-http
```

### Web Control Panel

The server includes a minimalist web interface for controlling all functions:

```bash
# Start with web interface
python server.py --web

# Access at http://localhost:8080
```

See [WEB_INTERFACE_GUIDE.md](WEB_INTERFACE_GUIDE.md) for detailed web interface and auto-start documentation.

### Transport Modes

The server supports multiple transport protocols:

- **stdio** (default): Standard input/output - compatible with OpenAI's MCP connectors
- **streamable-http**: HTTP-based transport at `http://localhost:8000/mcp`
- **sse**: Server-Sent Events transport
- **web**: Web control panel mode (use `--web` flag)

Set the default via `MCP_TRANSPORT` environment variable or use `--transport` flag.

### Auto-Start Setup

Configure the server to start automatically on boot:

```bash
# Install auto-start service (Linux)
sudo ./install-autostart.sh

# Start the service
sudo systemctl start cadslicerprinter@$USER.service

# Enable on boot
sudo systemctl enable cadslicerprinter@$USER.service
```

See [WEB_INTERFACE_GUIDE.md](WEB_INTERFACE_GUIDE.md) for Windows and macOS instructions.
