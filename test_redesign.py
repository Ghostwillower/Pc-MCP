#!/usr/bin/env python3
"""
Test script for the redesigned CadSlicerPrinter MCP server.

This script tests:
1. Configuration loading
2. Service initialization
3. Tool registration
4. Basic operations
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from config import get_settings
from services import CADService, SlicerService, PrinterService, WorkspaceService
from utils import sanitize_model_id, get_model_dir


def test_configuration():
    """Test configuration loading and validation."""
    print("Testing configuration...")
    
    settings = get_settings()
    assert settings is not None
    assert settings.workspace_dir is not None
    assert settings.mcp_transport in ["stdio", "sse", "streamable-http"]
    
    # Test validation
    messages = settings.validate()
    print(f"  Configuration validation messages: {len(messages)}")
    
    # Test ensure workspace
    settings.ensure_workspace()
    assert settings.workspace_dir.exists()
    assert settings.models_dir.exists()
    
    print("✓ Configuration tests passed")


def test_validation():
    """Test input validation."""
    print("\nTesting validation...")
    
    # Valid model IDs
    assert sanitize_model_id("abc123") == "abc123"
    assert sanitize_model_id("test-model_1") == "test-model_1"
    
    # Invalid model IDs should raise ValueError
    try:
        sanitize_model_id("../etc/passwd")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    
    try:
        sanitize_model_id("model with spaces")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    
    print("✓ Validation tests passed")


def test_services():
    """Test service initialization."""
    print("\nTesting services...")
    
    cad = CADService()
    assert cad.settings is not None
    
    slicer = SlicerService()
    assert slicer.settings is not None
    
    printer = PrinterService()
    assert printer.settings is not None
    
    workspace = WorkspaceService()
    assert workspace.settings is not None
    
    print("✓ Service initialization tests passed")


async def test_cad_operations():
    """Test CAD service operations."""
    print("\nTesting CAD operations...")
    
    cad = CADService()
    
    # Test model creation
    result = cad.create_model("Test model")
    assert "model_id" in result
    assert "scad_path" in result
    assert "error" not in result
    
    model_id = result["model_id"]
    print(f"  Created model: {model_id}")
    
    # Test getting code
    result = cad.get_code(model_id)
    assert "scad_code" in result
    assert "error" not in result
    print(f"  Retrieved code: {len(result['scad_code'])} chars")
    
    # Test updating parameters
    result = cad.update_parameters(model_id, {"width": 100, "height": 50})
    assert "updated" in result
    assert "width" in result["updated"]
    assert "height" in result["updated"]
    print(f"  Updated parameters: {result['updated']}")
    
    # Test listing previews (should be empty initially)
    result = cad.list_previews(model_id)
    assert "previews" in result
    assert len(result["previews"]) == 0
    print(f"  Listed previews: {len(result['previews'])}")
    
    print("✓ CAD operation tests passed")


async def test_workspace_operations():
    """Test workspace service operations."""
    print("\nTesting workspace operations...")
    
    workspace = WorkspaceService()
    
    # Test listing models
    result = workspace.list_models()
    assert "models" in result
    print(f"  Found {len(result['models'])} models in workspace")
    
    print("✓ Workspace operation tests passed")


async def main():
    """Run all tests."""
    print("=" * 70)
    print("CadSlicerPrinter MCP Server - Redesign Tests")
    print("=" * 70)
    
    try:
        # Synchronous tests
        test_configuration()
        test_validation()
        test_services()
        
        # Asynchronous tests
        await test_cad_operations()
        await test_workspace_operations()
        
        print("\n" + "=" * 70)
        print("✓ All tests passed!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
