# Pc-MCP
MCP servers for my PC

## CadSlicerPrinter MCP Server

A Python 3 MCP server that enables iterative 3D model design, preview, slicing, and printing through ChatGPT.

### Features

- **CAD Model Design**: Create and modify parametric OpenSCAD models using natural language
- **Preview Rendering**: Visualize models at any stage of the design process
- **Model Slicing**: Generate G-code using industry-standard slicers
- **3D Printer Control**: Upload and start print jobs via OctoPrint

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

# Run the server
cd src
python server.py
```

The server will start on `http://localhost:8000/mcp`.
