#!/usr/bin/env python3
"""
Test script to verify the iterative CAD workflow functionality.

This demonstrates the complete iterative design workflow:
1. Create a model
2. Get the code to see current parameters
3. Update parameters based on design requirements
4. Verify parameters were updated correctly
"""

import sys
import os
from pathlib import Path

# Add src directory to path for imports
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from server import (
    cad_create_model,
    cad_get_code,
    cad_update_parameters,
    cad_modify_model,
)


def test_iterative_workflow():
    """Test the complete iterative design workflow"""
    print("=" * 80)
    print("Testing Iterative CAD Workflow")
    print("=" * 80)
    
    # Step 1: Create a model
    print("\n[1] Creating initial model...")
    result = cad_create_model("Test parametric box for iteration testing")
    
    if "error" in result:
        print(f"  ✗ Error: {result['error']}")
        return False
    
    model_id = result["model_id"]
    print(f"  ✓ Model created: {model_id}")
    
    # Step 2: Get the initial code
    print("\n[2] Retrieving initial code...")
    code_result = cad_get_code(model_id)
    
    if "error" in code_result:
        print(f"  ✗ Error: {code_result['error']}")
        return False
    
    print(f"  ✓ Retrieved {len(code_result['scad_code'])} bytes of code")
    
    # Verify default parameters are present
    code = code_result['scad_code']
    if 'width = 50;' in code and 'height = 30;' in code:
        print("  ✓ Default parameters found (width=50, height=30)")
    else:
        print("  ✗ Default parameters not found in code")
        return False
    
    # Step 3: Update parameters (simulating AI comparing preview to target)
    print("\n[3] Updating parameters based on 'target design'...")
    update_result = cad_update_parameters(
        model_id,
        {
            "width": 80,
            "height": 50,
            "wall_thickness": 3,
            "enable_holes": True
        }
    )
    
    if "error" in update_result:
        print(f"  ✗ Error: {update_result['error']}")
        return False
    
    print(f"  ✓ Updated parameters: {update_result['updated']}")
    print(f"  ✓ Changes made:")
    for param, change in update_result['changes'].items():
        print(f"    - {param}: {change}")
    
    if update_result.get('not_found'):
        print(f"  ⚠ Parameters not found: {update_result['not_found']}")
    
    # Step 4: Verify the updates
    print("\n[4] Verifying parameter updates...")
    verify_result = cad_get_code(model_id)
    
    if "error" in verify_result:
        print(f"  ✗ Error: {verify_result['error']}")
        return False
    
    updated_code = verify_result['scad_code']
    
    # Check that parameters were actually updated
    checks = [
        ('width = 80;', 'width updated to 80'),
        ('height = 50;', 'height updated to 50'),
        ('wall_thickness = 3;', 'wall_thickness updated to 3'),
        ('enable_holes = true;', 'enable_holes set to true'),
    ]
    
    all_passed = True
    for check_str, description in checks:
        if check_str in updated_code:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ Failed: {description}")
            all_passed = False
    
    # Step 5: Test modification logging
    print("\n[5] Testing modification note logging...")
    mod_result = cad_modify_model(
        model_id,
        "Updated dimensions to match target design requirements"
    )
    
    if "error" in mod_result:
        print(f"  ✗ Error: {mod_result['error']}")
        return False
    
    print(f"  ✓ {mod_result['note']}")
    
    # Step 6: Test parameter update with non-existent parameter
    print("\n[6] Testing error handling for non-existent parameters...")
    bad_update = cad_update_parameters(
        model_id,
        {"nonexistent_param": 123}
    )
    
    if "error" in bad_update:
        print(f"  ✓ Correctly reported error: {bad_update['error']}")
    else:
        print(f"  ✗ Should have reported error for non-existent parameter")
        all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✓ All iterative workflow tests passed!")
        print("\nIterative Workflow Summary:")
        print("  1. ✓ Model creation")
        print("  2. ✓ Code retrieval")
        print("  3. ✓ Parameter updates")
        print("  4. ✓ Update verification")
        print("  5. ✓ Modification logging")
        print("  6. ✓ Error handling")
        print("\nThe MCP now supports full iterative CAD design:")
        print("  - AI can create initial models")
        print("  - AI can retrieve current code/parameters")
        print("  - AI can update parameters based on preview comparison")
        print("  - AI can iterate until design matches target")
    else:
        print("✗ Some tests failed")
    
    print("=" * 80)
    return all_passed


def main():
    """Run the iterative workflow test"""
    try:
        success = test_iterative_workflow()
        return 0 if success else 1
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
