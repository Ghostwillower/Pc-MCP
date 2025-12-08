# Getting Started with Pc-MCP

This guide will walk you through setting up and running the Pc-MCP (CadSlicerPrinter MCP Server) from scratch. Whether you're integrating with ChatGPT, using the web interface, or building your own MCP client, this guide has you covered.

## Table of Contents

- [Overview](#overview)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Server](#running-the-server)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Next Steps](#next-steps)

## Overview

The Pc-MCP server provides AI-assisted 3D modeling, slicing, and printing capabilities through the Model Context Protocol (MCP). It enables:

- **Iterative CAD Design**: Create and refine parametric 3D models with AI assistance
- **Preview Rendering**: Visualize models at any design stage
- **Model Slicing**: Generate G-code for 3D printing
- **Printer Control**: Upload and manage print jobs via OctoPrint
- **Filesystem Operations**: View and modify files on your computer
- **Terminal Commands**: Execute shell commands safely
- **Web Control Panel**: Browser-based interface for all features
- **OAuth Authentication**: Optional secure access control

## System Requirements

### Operating Systems

- **Linux**: Ubuntu 20.04+, Debian 11+, Fedora 35+, Arch Linux
- **macOS**: 11 (Big Sur) or later
- **Windows**: 10 or later (with WSL2 recommended for best compatibility)

### Required Software

1. **Python 3.10 or higher**
   - Check version: `python3 --version`
   - Download from: https://www.python.org/downloads/

2. **Git** (for cloning the repository)
   - Check version: `git --version`
   - Download from: https://git-scm.com/

3. **OpenSCAD** (for CAD model rendering)
   - **Linux**: `sudo apt install openscad` (Debian/Ubuntu) or `sudo dnf install openscad` (Fedora)
   - **macOS**: `brew install openscad` or download from https://openscad.org/
   - **Windows**: Download from https://openscad.org/downloads.html
   - Check installation: `openscad --version`

4. **3D Slicer** (one of the following):
   - **PrusaSlicer** (recommended): https://www.prusa3d.com/page/prusaslicer_424/
   - **OrcaSlicer**: https://github.com/SoftFever/OrcaSlicer
   - **CuraEngine**: https://github.com/Ultimaker/CuraEngine
   - **Slic3r**: https://slic3r.org/

### Optional Software

5. **OctoPrint** (for 3D printer control)
   - Only needed if you want to control a 3D printer
   - Download from: https://octoprint.org/
   - Can run on Raspberry Pi or any computer
   - Requires API key from OctoPrint settings

6. **Cloudflared** (for secure remote access)
   - Only needed for remote access via Cloudflare Tunnel
   - Download from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/

### Hardware Requirements

- **Minimum**: 2 GB RAM, 1 GB disk space
- **Recommended**: 4 GB RAM, 2 GB disk space
- **3D Printer**: Optional, any printer supported by OctoPrint

## Installation

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/Ghostwillower/Pc-MCP.git

# Navigate to the directory
cd Pc-MCP
```

### Step 2: Install Python Dependencies

Using pip (recommended):

```bash
# Install in development mode (allows you to modify the code)
pip install -e .

# Or install specific dependencies
pip install "mcp[cli]>=1.0.0" "httpx>=0.27.0" "authlib>=1.3.0" "itsdangerous>=2.1.0"
```

Using a virtual environment (recommended for isolation):

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Step 3: Verify Installation

```bash
# Check that Python can import MCP
python3 -c "import mcp; print('MCP installed successfully')"

# Check that the server file exists
ls -l src/server.py
```

## Configuration

### Basic Configuration

Create environment variables for the server. You can set these in your shell, or create a `.env` file.

#### Option 1: Export in Shell (Temporary)

```bash
# Required: Workspace directory for storing models and previews
export WORKSPACE_DIR="$HOME/Pc-MCP/workspace"

# Required: Path to OpenSCAD executable
export OPENSCAD_BIN="/usr/bin/openscad"

# Required: Path to slicer executable (adjust based on your slicer)
export SLICER_BIN="/usr/bin/prusa-slicer"  # Or /usr/bin/orca-slicer, etc.

# Optional: OctoPrint configuration (only if you have a 3D printer)
export OCTOPRINT_URL="http://localhost:5000"
export OCTOPRINT_API_KEY="your-api-key-here"

# Optional: Default transport mode (stdio for OpenAI, streamable-http for web)
export MCP_TRANSPORT="stdio"
```

#### Option 2: Create a Configuration Script (Permanent)

Create a file named `config.sh`:

```bash
#!/bin/bash
# Pc-MCP Configuration

# Workspace (where models are stored)
export WORKSPACE_DIR="$HOME/Pc-MCP/workspace"

# OpenSCAD binary location
# Find with: which openscad
export OPENSCAD_BIN="/usr/bin/openscad"

# Slicer binary location
# Find with: which prusa-slicer (or which orca-slicer, etc.)
export SLICER_BIN="/usr/bin/prusa-slicer"

# OctoPrint settings (optional - comment out if not using)
export OCTOPRINT_URL="http://localhost:5000"
export OCTOPRINT_API_KEY="your-api-key-here"

# Default transport mode
export MCP_TRANSPORT="stdio"
```

Make it executable and source it:

```bash
chmod +x config.sh
source config.sh
```

### Finding Binary Paths

If you're unsure where binaries are located:

```bash
# Find OpenSCAD
which openscad
# Common locations:
# Linux: /usr/bin/openscad
# macOS: /Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD
# Windows: C:\Program Files\OpenSCAD\openscad.exe

# Find your slicer
which prusa-slicer
which orca-slicer
which cura-engine
# Common locations:
# Linux: /usr/bin/prusa-slicer, /usr/local/bin/prusa-slicer
# macOS: /Applications/PrusaSlicer.app/Contents/MacOS/prusa-slicer
# Windows: C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer.exe
```

### Creating the Workspace Directory

```bash
# Create workspace directory
mkdir -p ~/Pc-MCP/workspace

# Verify it exists
ls -ld ~/Pc-MCP/workspace
```

### OctoPrint API Key (Optional)

If you want to control a 3D printer:

1. Open OctoPrint in your browser (usually http://localhost:5000 or your Raspberry Pi's IP)
2. Go to Settings (wrench icon) → Application Keys
3. Click "Generate" and give it a name like "Pc-MCP"
4. Copy the generated API key
5. Set it in your environment: `export OCTOPRINT_API_KEY="paste-key-here"`

## Running the Server

The server supports multiple modes depending on your use case:

### Mode 1: OpenAI/ChatGPT Integration (Default - stdio)

This is the recommended mode for ChatGPT and OpenAI MCP connectors:

```bash
cd src
python server.py
```

The server runs in stdio (standard input/output) mode, perfect for:
- ChatGPT integration via MCP connectors
- Claude Desktop integration
- Any MCP client using stdio transport

**Note**: In stdio mode, the server communicates through stdin/stdout. You won't see a web interface.

### Mode 2: Web Control Panel

Run the server with a browser-based control panel:

```bash
cd src
python server.py --web
```

Then open your browser to: http://localhost:8080

The web interface provides:
- CAD model creation and preview
- Slicer operations
- Printer control
- Workspace management
- Real-time output console

**Custom Port/Host:**
```bash
# Different port
python server.py --web --port 9000

# Allow remote access (security warning: exposes to network)
python server.py --web --host 0.0.0.0 --port 8080
```

### Mode 3: HTTP Transport (for web-based MCP clients)

Run with HTTP-based transport:

```bash
cd src
python server.py --transport streamable-http
```

Server endpoint: http://localhost:8000/mcp

This mode is for MCP clients that use HTTP instead of stdio.

### Mode 4: Server-Sent Events (SSE)

```bash
cd src
python server.py --transport sse
```

For MCP clients using Server-Sent Events.

### Mode 5: Auto-Start on Boot (Linux)

Configure the server to start automatically:

```bash
# Install systemd service
sudo ./install-autostart.sh

# Start the service
sudo systemctl start cadslicerprinter@$USER.service

# Enable on boot
sudo systemctl enable cadslicerprinter@$USER.service

# Check status
sudo systemctl status cadslicerprinter@$USER.service

# View logs
sudo journalctl -u cadslicerprinter@$USER.service -f
```

See [WEB_INTERFACE_GUIDE.md](WEB_INTERFACE_GUIDE.md) for Windows/macOS auto-start instructions.

## Verification

### Test 1: Server Starts Successfully

```bash
cd src
python server.py --web
```

You should see:
```
INFO - Server starting on http://127.0.0.1:8080
INFO - Web control panel enabled
```

### Test 2: Web Interface Loads

1. Start the server with `--web` flag
2. Open http://localhost:8080 in your browser
3. You should see the control panel interface

### Test 3: Create a Simple Model

Using the web interface:

1. Go to the "Create Model" section
2. Enter: "Create a simple cube that is 20mm on each side"
3. Click "Create Model"
4. Note the model ID in the output panel

### Test 4: Render a Preview

1. Use the model ID from Test 3
2. Go to "Render Preview" section
3. Enter the model ID
4. Click "Render Preview"
5. The output should show a PNG file path

### Test 5: Check Workspace

```bash
# List workspace contents
ls -la ~/Pc-MCP/workspace/

# You should see:
# - .scad files (models)
# - .png files (previews)
```

### Test 6: Verify External Tools

```bash
# Test OpenSCAD
$OPENSCAD_BIN --version

# Test Slicer
$SLICER_BIN --version

# Test OctoPrint connection (if configured)
curl -H "X-Api-Key: $OCTOPRINT_API_KEY" $OCTOPRINT_URL/api/version
```

## Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'mcp'"

**Solution**: Install the dependencies
```bash
pip install -e .
# Or
pip install "mcp[cli]>=1.0.0"
```

### Problem: "OpenSCAD binary not found"

**Solution**: Check your OPENSCAD_BIN path
```bash
# Find OpenSCAD
which openscad

# Set the correct path
export OPENSCAD_BIN="/path/to/openscad"

# Test it
$OPENSCAD_BIN --version
```

### Problem: "Permission denied" when creating workspace

**Solution**: Create the directory with proper permissions
```bash
mkdir -p ~/Pc-MCP/workspace
chmod 755 ~/Pc-MCP/workspace
```

### Problem: Web interface shows "Connection failed"

**Solutions**:
1. Check that the server is running: `ps aux | grep server.py`
2. Verify the port is not in use: `lsof -i :8080`
3. Check firewall settings
4. Try a different port: `python server.py --web --port 9000`

### Problem: "Could not connect to OctoPrint"

**Solutions**:
1. Verify OctoPrint is running: Open http://localhost:5000 in browser
2. Check API key is correct: Go to OctoPrint Settings → Application Keys
3. Verify URL is correct: `export OCTOPRINT_URL="http://localhost:5000"`
4. Test connection: `curl -H "X-Api-Key: $OCTOPRINT_API_KEY" $OCTOPRINT_URL/api/version`

### Problem: Slicer fails with "command not found"

**Solution**: Check slicer binary path
```bash
# Find your slicer
which prusa-slicer
which orca-slicer

# Update environment variable
export SLICER_BIN="/correct/path/to/slicer"
```

### Problem: Server won't start - "Address already in use"

**Solution**: Another process is using the port
```bash
# Find what's using port 8080
lsof -i :8080

# Kill the process (use the PID from above)
kill <PID>

# Or use a different port
python server.py --web --port 9000
```

### Problem: Models aren't being created

**Solution**: Check workspace permissions and environment
```bash
# Verify workspace exists and is writable
ls -ld $WORKSPACE_DIR
mkdir -p $WORKSPACE_DIR

# Check environment variables
echo $WORKSPACE_DIR
echo $OPENSCAD_BIN
echo $SLICER_BIN

# Check server logs for errors
```

### Problem: Preview rendering fails

**Solution**: Verify OpenSCAD is working
```bash
# Test OpenSCAD directly
$OPENSCAD_BIN --version

# Try rendering a test file
echo "cube([10,10,10]);" > test.scad
$OPENSCAD_BIN -o test.png test.scad
ls -l test.png
rm test.scad test.png
```

### Getting Help

If you're still having issues:

1. **Check the logs**: Look for error messages in the server output
2. **Review documentation**: 
   - [ARCHITECTURE.md](ARCHITECTURE.md) - Server architecture
   - [WEB_INTERFACE_GUIDE.md](WEB_INTERFACE_GUIDE.md) - Web interface details
   - [OAUTH_GUIDE.md](OAUTH_GUIDE.md) - OAuth configuration
   - [FILESYSTEM_TERMINAL_GUIDE.md](FILESYSTEM_TERMINAL_GUIDE.md) - File and terminal operations
3. **Check GitHub issues**: https://github.com/Ghostwillower/Pc-MCP/issues
4. **Enable debug logging**: Add `--debug` flag when starting the server

## Next Steps

Now that you have the server running, explore the full capabilities:

### For ChatGPT/OpenAI Users

See [OPENAI_INTEGRATION.md](OPENAI_INTEGRATION.md) for:
- Configuring MCP connectors in ChatGPT
- Using the server with OpenAI's API
- Best practices for AI-assisted 3D modeling

### For Web Interface Users

See [WEB_INTERFACE_GUIDE.md](WEB_INTERFACE_GUIDE.md) for:
- Detailed web interface features
- Auto-start configuration
- Remote access setup with Cloudflare Tunnel

### For Iterative Design

See [ITERATIVE_WORKFLOW_GUIDE.md](ITERATIVE_WORKFLOW_GUIDE.md) for:
- AI-driven iterative design workflow
- Creating parametric models
- Refining designs based on visual feedback

### For Filesystem and Terminal Operations

See [FILESYSTEM_TERMINAL_GUIDE.md](FILESYSTEM_TERMINAL_GUIDE.md) for:
- Filesystem operations (read, write, list, delete files)
- Terminal command execution
- Security controls and limitations

### For OAuth Authentication

See [OAUTH_GUIDE.md](OAUTH_GUIDE.md) for:
- Setting up OAuth providers (Google, GitHub, Auth0)
- Securing your server with authentication
- Session management

### For Developers

See [ARCHITECTURE.md](ARCHITECTURE.md) for:
- Server architecture and design
- Adding new tools and services
- Contributing to the project

### Building MCP Servers

See [CHATGPT_MCP_GUIDE.md](CHATGPT_MCP_GUIDE.md) for:
- Understanding the Model Context Protocol
- Building your own MCP servers
- Integration best practices

## Quick Reference

### Common Commands

```bash
# Start with web interface
cd src && python server.py --web

# Start for OpenAI/ChatGPT
cd src && python server.py

# Start with HTTP transport
cd src && python server.py --transport streamable-http

# Auto-start service (Linux)
sudo systemctl start cadslicerprinter@$USER.service
sudo systemctl status cadslicerprinter@$USER.service
```

### Environment Variables

```bash
export WORKSPACE_DIR="$HOME/Pc-MCP/workspace"
export OPENSCAD_BIN="/usr/bin/openscad"
export SLICER_BIN="/usr/bin/prusa-slicer"
export OCTOPRINT_URL="http://localhost:5000"
export OCTOPRINT_API_KEY="your-api-key"
export MCP_TRANSPORT="stdio"
```

### Port and Host Options

```bash
--port 8080          # Web server port (default: 8080)
--host 127.0.0.1     # Web server host (default: 127.0.0.1)
--web                # Enable web control panel
--transport stdio    # Transport mode (stdio, sse, streamable-http)
```

## Support and Community

- **GitHub**: https://github.com/Ghostwillower/Pc-MCP
- **Issues**: https://github.com/Ghostwillower/Pc-MCP/issues
- **Documentation**: See the `*.md` files in the repository root

---

**Congratulations!** You now have Pc-MCP up and running. Happy 3D modeling! 🎉
