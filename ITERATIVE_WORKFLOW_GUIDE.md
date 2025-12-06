# Iterative CAD Design Workflow Guide

This guide explains how to use the CadSlicerPrinter MCP server's iterative design capabilities to refine 3D models based on visual feedback.

## Overview

The iterative design workflow enables AI assistants (like ChatGPT) to:
1. Generate initial parametric CAD models
2. Render preview images to see the current design
3. Compare previews against target requirements
4. Update specific parameters based on differences
5. Repeat steps 2-4 until the design matches the target

This creates a visual feedback loop where the AI can "see" what it's designing and make informed adjustments.

## The Iterative Workflow

### 1. Create Initial Model

Start by creating a parametric model from a description:

```python
result = cad_create_model("A phone stand with adjustable viewing angle")
model_id = result["model_id"]
```

The server generates an OpenSCAD file with modifiable parameters like:
- `width`, `depth`, `height` - Basic dimensions
- `wall_thickness` - Structural parameters
- `enable_holes`, `enable_base` - Feature toggles
- `corner_radius` - Aesthetic parameters

### 2. Render Preview Image

Generate a PNG preview to see what the current design looks like:

```python
result = cad_render_preview(model_id, view="iso", width=1024, height=768)
png_path = result["png_path"]
```

The AI can then "view" this image to understand the current model state.

### 3. Inspect Current Parameters

Retrieve the SCAD code to see available parameters and their current values:

```python
result = cad_get_code(model_id)
print(result["scad_code"])
```

This shows the AI what parameters exist and what values can be modified.

### 4. Compare and Update

The AI compares the preview to the target design and updates parameters accordingly:

```python
# AI determines: "The base is too narrow for stability"
result = cad_update_parameters(model_id, {
    "width": 80,   # Increase from 50
    "depth": 80    # Increase from 50
})

# AI determines: "Height is insufficient for the phone"
result = cad_update_parameters(model_id, {
    "height": 50,         # Increase from 30
    "enable_holes": True  # Add mounting holes
})
```

Each update shows what changed:
```python
{
    "updated": ["width", "depth"],
    "changes": {
        "width": "50 -> 80",
        "depth": "50 -> 80"
    }
}
```

### 5. Iterate Until Perfect

Repeat steps 2-4 until the preview matches the target design:

```
Iteration 1: Preview shows base too narrow
  → Update: width=80, depth=80
  
Iteration 2: Preview shows height insufficient
  → Update: height=50
  
Iteration 3: Preview shows design matches target
  → Done! Proceed to slicing
```

## Complete Example

Here's a complete iterative design session:

```python
from server import (
    cad_create_model,
    cad_render_preview,
    cad_get_code,
    cad_update_parameters,
)

# 1. Create initial model
result = cad_create_model("Ergonomic phone stand for desk use")
model_id = result["model_id"]

# 2. See initial design
preview = cad_render_preview(model_id)
# AI views preview, sees it's too small

# 3. Iteration 1: Increase base dimensions
cad_update_parameters(model_id, {
    "width": 80,
    "depth": 80
})

# 4. Check updated design
preview = cad_render_preview(model_id)
# AI views preview, sees height is insufficient

# 5. Iteration 2: Increase height and add stability features
cad_update_parameters(model_id, {
    "height": 50,
    "wall_thickness": 3,
    "enable_base": True
})

# 6. Final check
preview = cad_render_preview(model_id)
# AI views preview, design matches target!

# 7. Proceed to slicing and printing
# ...
```

## Available Tools

### Core Iterative Design Tools

1. **cad_create_model(description)** - Generate initial parametric model
2. **cad_render_preview(model_id, view, width, height)** - Create preview PNG
3. **cad_get_code(model_id)** - Retrieve current SCAD code
4. **cad_update_parameters(model_id, parameters)** - Update specific parameters
5. **cad_list_previews(model_id)** - List all preview images (iteration history)

### Supporting Tools

6. **cad_modify_model(model_id, instruction)** - Log modification notes
7. **workspace_list_models()** - View all models in workspace

### Production Tools

8. **slicer_slice_model(model_id, profile, extra_args)** - Generate G-code
9. **printer_upload_and_start(model_id)** - Upload and print
10. **printer_status()** - Check printer state
11. **printer_send_gcode_line(gcode)** - Send manual commands

## Parameter Types

The `cad_update_parameters` tool handles different parameter types automatically:

### Numeric Parameters
```python
cad_update_parameters(model_id, {
    "width": 80,          # Integer
    "wall_thickness": 2.5  # Float
})
```

### Boolean Parameters
```python
cad_update_parameters(model_id, {
    "enable_holes": True,
    "enable_base": False
})
```

### String Parameters
```python
cad_update_parameters(model_id, {
    "label": "My Design"
})
```

## Best Practices

### For AI Assistants

1. **Always preview before iterating** - Render a preview to see what needs changing
2. **Update specific parameters** - Use `cad_update_parameters` for precise changes
3. **Iterate incrementally** - Make small changes and preview after each iteration
4. **Verify changes** - Use `cad_get_code` to confirm parameter updates
5. **Track history** - Use `cad_list_previews` to see iteration history

### Common Iteration Patterns

#### Size Adjustment
```python
# Preview shows model is too small
cad_update_parameters(model_id, {
    "width": 100,
    "height": 75,
    "depth": 100
})
```

#### Feature Refinement
```python
# Preview shows need for structural improvements
cad_update_parameters(model_id, {
    "wall_thickness": 3,
    "corner_radius": 5,
    "enable_base": True
})
```

#### Aesthetic Tweaks
```python
# Preview shows rough appearance
cad_update_parameters(model_id, {
    "corner_radius": 8,
    "enable_holes": True
})
```

## Error Handling

### Parameter Not Found
```python
result = cad_update_parameters(model_id, {
    "nonexistent_param": 123
})
# Returns: {"error": "No parameters updated", "not_found": ["nonexistent_param"]}
```

**Solution**: Use `cad_get_code()` to see available parameters

### Model Not Found
```python
result = cad_get_code("invalid_id")
# Returns: {"error": "Model not found"}
```

**Solution**: Use `workspace_list_models()` to see available models

### Preview Rendering Failed
```python
result = cad_render_preview(model_id)
# Returns: {"error": "OpenSCAD rendering failed", "details": "..."}
```

**Solution**: Check that OPENSCAD_BIN is configured correctly

## OpenAI MCP Integration

The server uses stdio transport by default for seamless OpenAI MCP integration:

```bash
# Run server in OpenAI-compatible mode (default)
cd src
python server.py

# The server automatically uses stdio transport
# OpenAI MCP connectors can communicate via JSON-RPC messages
```

All tools return JSON-serializable dictionaries, making them compatible with:
- OpenAI's ChatGPT with MCP support
- Claude Desktop with MCP support
- Any other MCP-compatible AI client

## Configuration

For full iterative workflow functionality, configure these environment variables:

```bash
export WORKSPACE_DIR="./workspace"        # Model storage location
export OPENSCAD_BIN="/usr/bin/openscad"  # Required for previews
export SLICER_BIN="/usr/bin/prusa-slicer" # Required for G-code
export OCTOPRINT_URL="http://localhost:5000"  # Optional: printer control
export OCTOPRINT_API_KEY="your-key"      # Optional: printer control
```

Minimum configuration for iterative design:
- `WORKSPACE_DIR` - Defaults to ./workspace
- `OPENSCAD_BIN` - Required for preview rendering

## Summary

The iterative design workflow transforms AI-CAD interaction from "generate and hope" to "generate, see, refine, repeat" - enabling true visual feedback-driven design refinement.

Key capabilities:
- ✅ Create parametric models from descriptions
- ✅ Render preview images at any iteration
- ✅ Inspect current parameter values
- ✅ Update specific parameters precisely
- ✅ Iterate until design matches target
- ✅ Full OpenAI MCP compatibility

This enables AI assistants to design 3D models with the same iterative refinement process that human designers use.
