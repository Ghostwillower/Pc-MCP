# Pc-MCP
MCP servers for my PC

## Documentation

- **[Building MCP Servers for ChatGPT](CHATGPT_MCP_GUIDE.md)** - Comprehensive guide to building MCP servers compatible with ChatGPT and API integrations
- **[OpenAI Integration](OPENAI_INTEGRATION.md)** - Quick guide for integrating this server with OpenAI's MCP connectors
- **[Architecture](ARCHITECTURE.md)** - Server architecture and design principles
- **[Web Interface Guide](WEB_INTERFACE_GUIDE.md)** - Web control panel and auto-start setup
- **[Filesystem and Terminal Tools](FILESYSTEM_TERMINAL_GUIDE.md)** - Guide to filesystem operations and terminal command execution
- **[OAuth Configuration](OAUTH_GUIDE.md)** - Guide to configuring OAuth authentication for secure access

## CadSlicerPrinter MCP Server

A Python 3 MCP server that enables iterative 3D model design, preview, slicing, and printing through ChatGPT and other MCP-compatible clients, or via the included web control panel.

**✨ Recently redesigned for maximum backend efficiency** - See [ARCHITECTURE.md](ARCHITECTURE.md) for details.

### Key Improvements (v0.2.0)

- 🚀 **74% reduction** in main server code (1461 → 381 lines)
- ⚡ **Async operations** for rendering, slicing, and HTTP requests
- 🔌 **Connection pooling** for OctoPrint API (reduces latency)
- 💾 **Configuration caching** for faster access
- 🏗️ **Modular architecture** (config, services, tools, utils)
- ✅ **Zero feature loss** - fully backward compatible

### Features

- **Iterative CAD Design**: AI-driven iterative model refinement with visual feedback loop
  - Create parametric OpenSCAD models from natural language descriptions
  - Retrieve current model parameters and code
  - Update parameters based on comparing preview images to target design
  - Iterate until the model matches the desired output
- **Preview Rendering**: Visualize models at any stage of the design process
- **Model Slicing**: Generate G-code using industry-standard slicers
- **3D Printer Control**: Upload and start print jobs via OctoPrint
- **Filesystem Operations**: View and modify files on your computer
  - Read and write files with security controls
  - List directory contents
  - Create and delete files/directories
  - Get file information and metadata
- **Terminal Commands**: Execute shell commands safely without admin privileges
  - Run development tools, scripts, and utilities
  - Build and test code
  - Security controls block privileged operations (sudo, systemctl, etc.)
- **Web Control Panel**: Minimalist web interface for controlling all functions
- **OAuth Authentication**: Optional OAuth 2.0 authentication for secure access control
- **Cloudflared Tunnel Support**: Optional Cloudflare Tunnel integration for secure remote access
- **Auto-Start Support**: Run as a system service on boot without GUI
- **OpenAI Compatible**: Uses stdio transport for seamless integration with OpenAI's MCP connectors

### Iterative Design Workflow

The server enables true AI-driven iterative design:

1. **Create** - AI generates initial parametric model from description
2. **Preview** - System renders PNG image of current model state
3. **Compare** - AI compares preview to target design requirements
4. **Update** - AI modifies specific parameters based on differences
5. **Repeat** - Steps 2-4 iterate until design matches target

Example iteration:
```
AI: Creates phone stand → Preview shows it's too narrow
AI: Updates width from 50mm to 80mm → Preview confirms improvement
AI: Updates angle from 45° to 60° → Preview matches target design
```

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
