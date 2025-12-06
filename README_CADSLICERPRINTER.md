# CadSlicerPrinter MCP Server

A Python 3 MCP server that enables iterative 3D model design, preview, slicing, and printing through ChatGPT.

## Features

- **CAD Model Design**: Create and modify parametric OpenSCAD models using natural language
- **Preview Rendering**: Visualize models at any stage of the design process
- **Model Slicing**: Generate G-code using industry-standard slicers (PrusaSlicer, Orca, CuraEngine)
- **3D Printer Control**: Upload and start print jobs via OctoPrint

## Installation

### Prerequisites

- Python 3.10 or higher
- OpenSCAD (for CAD rendering)
- A slicer CLI (PrusaSlicer, OrcaSlicer, or CuraEngine)
- OctoPrint (optional, for printer control)

### Install Dependencies

```bash
pip install -e .
```

Or using pip directly:

```bash
pip install "mcp[cli]>=1.0.0" "requests>=2.31.0"
```

## Configuration

Set the following environment variables:

```bash
# Required for CAD features
export WORKSPACE_DIR="./workspace"          # Directory for models and previews
export OPENSCAD_BIN="/usr/bin/openscad"     # Path to OpenSCAD executable

# Required for slicing
export SLICER_BIN="/usr/bin/prusa-slicer"   # Path to slicer CLI

# Required for printer control (optional)
export OCTOPRINT_URL="http://localhost:5000"
export OCTOPRINT_API_KEY="your-api-key-here"
```

## Running the Server

```bash
cd src
python server.py
```

The server will start on `http://localhost:8000/mcp`.

## Usage Workflow

### 1. Create a Model

```python
# Through MCP client
result = mcp.call_tool("cad_create_model", {
    "description": "A parametric phone stand with adjustable angle"
})
# Returns: {"model_id": "abc123", "scad_path": "/path/to/main.scad"}
```

### 2. Preview the Model

```python
result = mcp.call_tool("cad_render_preview", {
    "model_id": "abc123",
    "view": "iso",
    "width": 1024,
    "height": 768
})
# Returns: {"model_id": "abc123", "png_path": "/path/to/preview.png"}
```

### 3. Modify the Design

```python
result = mcp.call_tool("cad_modify_model", {
    "model_id": "abc123",
    "instruction": "Increase the base width to 80mm"
})
# Returns: {"model_id": "abc123", "scad_path": "...", "note": "..."}
```

### 4. Slice for Printing

```python
result = mcp.call_tool("slicer_slice_model", {
    "model_id": "abc123",
    "profile": "/path/to/printer-profile.ini",
    "extra_args": {"layer-height": "0.2"}
})
# Returns: {"model_id": "abc123", "gcode_path": "/path/to/model.gcode"}
```

### 5. Upload and Print

```python
# Check printer status first
status = mcp.call_tool("printer_status", {})

# Upload and start printing
result = mcp.call_tool("printer_upload_and_start", {
    "model_id": "abc123"
})
```

## Available Tools

### CAD Tools

- `cad_create_model(description)` - Generate initial parametric CAD file
- `cad_modify_model(model_id, instruction)` - Iteratively refine the model
- `cad_render_preview(model_id, view, width, height)` - Render preview PNG
- `cad_list_previews(model_id)` - List available preview images

### Slicer Tools

- `slicer_slice_model(model_id, profile, extra_args)` - Slice model to G-code

### Printer Tools

- `printer_status()` - Get current printer status
- `printer_upload_and_start(model_id)` - Upload G-code and start printing
- `printer_send_gcode_line(gcode)` - Send single G-code command (⚠️ use with caution)

### Workspace Tools

- `workspace_list_models()` - List all models in workspace

## Directory Structure

```
workspace/
└── models/
    ├── abc123/
    │   ├── main.scad           # OpenSCAD source
    │   ├── model.stl           # Generated STL
    │   ├── model.gcode         # Sliced G-code
    │   ├── preview_1234.png    # Preview renders
    │   └── preview_5678.png
    └── def456/
        └── ...
```

## Safety & Security

- All model files are restricted to the `WORKSPACE_DIR`
- Model IDs are sanitized to prevent directory traversal
- No arbitrary command execution is exposed
- External tools (OpenSCAD, slicer) are only called with validated paths
- OctoPrint commands require API key authentication

## Troubleshooting

### "OPENSCAD_BIN not configured"

Set the `OPENSCAD_BIN` environment variable to point to your OpenSCAD executable.

### "SLICER_BIN not configured"

Set the `SLICER_BIN` environment variable to point to your slicer CLI executable.

### "OCTOPRINT_API_KEY not configured"

Set both `OCTOPRINT_URL` and `OCTOPRINT_API_KEY` environment variables to use printer features.

### Preview rendering fails

Check that:
1. OpenSCAD is installed and accessible
2. The SCAD file has valid syntax
3. The `WORKSPACE_DIR` has write permissions

## License

This project is part of the Pc-MCP repository.
