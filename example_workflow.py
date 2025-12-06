#!/usr/bin/env python3
"""
Example script demonstrating the CadSlicerPrinter MCP server workflow.

This script shows how to use the server tools for a complete design-to-print workflow.
Note: This is a demonstration script. In practice, these tools would be called
by an MCP client (like ChatGPT) through the MCP protocol.
"""

import os
import sys
sys.path.insert(0, 'src')

from server import (
    cad_create_model,
    cad_render_preview,
    cad_modify_model,
    cad_list_previews,
    slicer_slice_model,
    workspace_list_models,
    printer_status,
)


def main():
    print("=" * 80)
    print("CadSlicerPrinter MCP Server - Example Workflow")
    print("=" * 80)
    
    # Step 1: Create a model
    print("\n[1] Creating a parametric model...")
    result = cad_create_model("A parametric phone stand with adjustable viewing angle")
    
    if "error" in result:
        print(f"  ✗ Error: {result['error']}")
        return
    
    model_id = result["model_id"]
    print(f"  ✓ Model created: {model_id}")
    print(f"  ✓ SCAD file: {result['scad_path']}")
    
    # Step 2: Modify the model
    print("\n[2] Modifying the model...")
    mod_result = cad_modify_model(
        model_id,
        "Increase the base width to 80mm for better stability"
    )
    
    if "error" in mod_result:
        print(f"  ✗ Error: {mod_result['error']}")
    else:
        print(f"  ✓ {mod_result['note']}")
    
    # Step 3: List previews (none yet, but demonstrates the API)
    print("\n[3] Checking for previews...")
    prev_result = cad_list_previews(model_id)
    
    if "error" in prev_result:
        print(f"  ✗ Error: {prev_result['error']}")
    else:
        print(f"  ✓ Found {len(prev_result['previews'])} preview(s)")
        
        # Note: To actually render a preview, you would call:
        # render_result = cad_render_preview(model_id, view="iso", width=1024, height=768)
        # But this requires OpenSCAD to be installed
        print("  ℹ To render preview: cad_render_preview(model_id, 'iso', 1024, 768)")
    
    # Step 4: List workspace models
    print("\n[4] Listing workspace models...")
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
    
    # Step 5: Check printer status (will fail without OctoPrint configured)
    print("\n[5] Checking printer status...")
    printer_result = printer_status()
    
    if "error" in printer_result:
        print(f"  ⚠ {printer_result['error']}")
        print(f"  ℹ Configure OCTOPRINT_URL and OCTOPRINT_API_KEY to use printer features")
    else:
        print(f"  ✓ Printer status retrieved")
        if "job" in printer_result:
            print(f"    Job state: {printer_result['job'].get('state', 'unknown')}")
        if "printer" in printer_result:
            print(f"    Printer state: {printer_result['printer'].get('state', {}).get('text', 'unknown')}")
    
    # Summary
    print("\n" + "=" * 80)
    print("Workflow Summary:")
    print("  ✓ Model created and stored")
    print("  ✓ Model modification logged")
    print("  ℹ Next steps (require external tools):")
    print("    1. Set OPENSCAD_BIN environment variable")
    print("    2. Call cad_render_preview() to see your model")
    print("    3. Set SLICER_BIN and call slicer_slice_model()")
    print("    4. Set OCTOPRINT_API_KEY and call printer_upload_and_start()")
    print("=" * 80)
    
    print(f"\n✓ Example completed successfully!")
    print(f"  Model ID: {model_id}")
    print(f"  Model directory: workspace/models/{model_id}/")


if __name__ == "__main__":
    main()
