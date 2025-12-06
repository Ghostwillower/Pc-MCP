#!/usr/bin/env python3
"""
Example script demonstrating the iterative CAD workflow in the CadSlicerPrinter MCP server.

This script shows how an AI client (like ChatGPT) can iteratively refine a 3D model
by comparing preview images to target requirements and updating parameters accordingly.

The workflow simulates:
1. Initial model creation
2. Preview rendering to see current state
3. Code inspection to understand available parameters
4. Parameter updates based on design comparison
5. Iteration until design matches target
"""

import os
import sys
sys.path.insert(0, 'src')

from server import (
    cad_create_model,
    cad_get_code,
    cad_update_parameters,
    cad_render_preview,
    cad_list_previews,
    slicer_slice_model,
    workspace_list_models,
    printer_status,
)


def main():
    print("=" * 80)
    print("CadSlicerPrinter MCP Server - Iterative Design Workflow Example")
    print("=" * 80)
    
    # Step 1: Create initial model
    print("\n[1] Creating initial parametric model...")
    result = cad_create_model("A parametric phone stand with adjustable viewing angle")
    
    if "error" in result:
        print(f"  ✗ Error: {result['error']}")
        return
    
    model_id = result["model_id"]
    print(f"  ✓ Model created: {model_id}")
    print(f"  ✓ SCAD file: {result['scad_path']}")
    
    # Step 2: Get current code to see what parameters are available
    print("\n[2] Inspecting model parameters...")
    code_result = cad_get_code(model_id)
    
    if "error" in code_result:
        print(f"  ✗ Error: {code_result['error']}")
    else:
        print(f"  ✓ Retrieved model code ({len(code_result['scad_code'])} bytes)")
        # Extract and display parameter section
        code = code_result['scad_code']
        if "// PARAMETERS" in code:
            param_section = code.split("// MODEL DEFINITION")[0]
            print("  ✓ Available parameters found")
        else:
            print("  ✓ Model code retrieved")
    
    # Step 3: Simulate iterative refinement
    print("\n[3] Simulating iterative design refinement...")
    
    # Iteration 1: AI would render preview, compare to target, decide to increase width
    print("\n  Iteration 1: Adjusting base dimensions")
    print("    (Simulated: AI sees preview is too narrow, needs more stability)")
    
    update1 = cad_update_parameters(
        model_id,
        {
            "width": 80,  # Increase from default 50
            "depth": 80,  # Increase from default 50
        }
    )
    
    if "error" not in update1:
        print(f"    ✓ Updated: {', '.join(update1['updated'])}")
        for param, change in update1.get('changes', {}).items():
            print(f"      - {param}: {change}")
    else:
        print(f"    ✗ {update1['error']}")
    
    # Iteration 2: AI would render new preview, see it needs more height
    print("\n  Iteration 2: Adjusting height and features")
    print("    (Simulated: AI compares new preview to target, adjusts height)")
    
    update2 = cad_update_parameters(
        model_id,
        {
            "height": 50,          # Increase from default 30
            "wall_thickness": 3,   # Increase from default 2
            "enable_holes": True,  # Enable mounting holes
        }
    )
    
    if "error" not in update2:
        print(f"    ✓ Updated: {', '.join(update2['updated'])}")
        for param, change in update2.get('changes', {}).items():
            print(f"      - {param}: {change}")
    else:
        print(f"    ✗ {update2['error']}")
    
    # Step 4: Verify final parameters
    print("\n[4] Verifying final model state...")
    final_code = cad_get_code(model_id)
    
    if "error" not in final_code:
        code = final_code['scad_code']
        checks = [
            ("width = 80;", "Width set to 80mm"),
            ("depth = 80;", "Depth set to 80mm"),
            ("height = 50;", "Height set to 50mm"),
            ("wall_thickness = 3;", "Wall thickness set to 3mm"),
            ("enable_holes = true;", "Mounting holes enabled"),
        ]
        
        print("  Final parameter values:")
        for check_str, description in checks:
            if check_str in code:
                print(f"    ✓ {description}")
    
    # Step 5: List previews (would show iteration history if rendered)
    print("\n[5] Checking preview history...")
    prev_result = cad_list_previews(model_id)
    
    if "error" in prev_result:
        print(f"  ✗ Error: {prev_result['error']}")
    else:
        print(f"  ✓ Found {len(prev_result['previews'])} preview(s)")
        
        # Note about rendering
        print("\n  ℹ To render preview (requires OpenSCAD):")
        print(f"    result = cad_render_preview('{model_id}', view='iso', width=1024, height=768)")
        print("    This would generate a PNG showing the current model state")
    
    # Step 6: List workspace models
    print("\n[6] Workspace summary...")
    ws_result = workspace_list_models()
    
    if "error" in ws_result:
        print(f"  ✗ Error: {ws_result['error']}")
    else:
        print(f"  ✓ Total models in workspace: {len(ws_result['models'])}")
        for model in ws_result['models']:
            print(f"    - {model['model_id']}: "
                  f"SCAD={'✓' if model['scad_exists'] else '✗'}, "
                  f"GCODE={'✓' if model['gcode_exists'] else '✗'}, "
                  f"Previews={model['previews']}")
    
    # Step 7: Next steps for full workflow
    print("\n" + "=" * 80)
    print("Iterative Design Workflow Summary:")
    print("=" * 80)
    print("  ✓ Model created with parametric design")
    print("  ✓ Parameters inspected via code retrieval")
    print("  ✓ Multiple iterations of parameter updates")
    print("  ✓ Changes verified in final code")
    print("")
    print("Complete Workflow (with external tools configured):")
    print("  1. cad_create_model() - Generate initial design")
    print("  2. cad_render_preview() - See current state")
    print("  3. cad_get_code() - Inspect parameters")
    print("  4. cad_update_parameters() - Refine based on comparison")
    print("  5. Repeat steps 2-4 until design matches target")
    print("  6. slicer_slice_model() - Generate G-code")
    print("  7. printer_upload_and_start() - Begin printing")
    print("")
    print("Configuration needed for full functionality:")
    print("  - OPENSCAD_BIN: Path to OpenSCAD for preview rendering")
    print("  - SLICER_BIN: Path to slicer for G-code generation")
    print("  - OCTOPRINT_URL & OCTOPRINT_API_KEY: For printer control")
    print("=" * 80)
    
    print(f"\n✓ Example completed successfully!")
    print(f"  Model ID: {model_id}")
    print(f"  Model directory: workspace/models/{model_id}/")
    print(f"\n💡 Key Innovation: AI can now iteratively refine models by:")
    print(f"  - Viewing previews to see current design")
    print(f"  - Comparing to target requirements")
    print(f"  - Updating specific parameters")
    print(f"  - Repeating until design is perfect!")


if __name__ == "__main__":
    main()
