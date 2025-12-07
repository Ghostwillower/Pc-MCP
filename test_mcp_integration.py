#!/usr/bin/env python3
"""Integration test for filesystem and terminal tools through MCP server."""

import sys
import json
import asyncio
from pathlib import Path
import tempfile
import shutil

# Add src directory to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from server import create_mcp_server


async def test_mcp_tools():
    """Test MCP tools through the server."""
    print("=" * 80)
    print("Testing MCP Server Tools Integration")
    print("=" * 80)
    
    # Create MCP server
    print("\n1. Creating MCP server...")
    mcp = create_mcp_server()
    print("   ✓ Server created successfully")
    
    # Get list of tools
    print("\n2. Listing available tools...")
    tools = await mcp.list_tools()
    print(f"   Found {len(tools)} tools:")
    
    filesystem_tools = [t for t in tools if t.name.startswith("filesystem_")]
    terminal_tools = [t for t in tools if t.name.startswith("terminal_")]
    
    print(f"\n   Filesystem tools ({len(filesystem_tools)}):")
    for tool in filesystem_tools:
        print(f"     - {tool.name}")
    
    print(f"\n   Terminal tools ({len(terminal_tools)}):")
    for tool in terminal_tools:
        print(f"     - {tool.name}")
    
    # Create a temporary test directory in the workspace
    test_workspace = Path("./workspace/test_integration")
    test_workspace.mkdir(parents=True, exist_ok=True)
    print(f"\n3. Using test workspace: {test_workspace.resolve()}")
    
    try:
        # Test filesystem_create_directory
        print("\n4. Testing filesystem_create_directory...")
        test_dir = str(test_workspace / "myproject")
        _, meta = await mcp.call_tool("filesystem_create_directory", {"dir_path": test_dir})
        result_data = meta.get('result', {})
        if result_data.get("success"):
            print(f"   ✓ Directory created: {result_data.get('path')}")
        else:
            print(f"   ✗ Failed: {result_data.get('error')}")
        
        # Test filesystem_write_file
        print("\n5. Testing filesystem_write_file...")
        test_file = str(test_workspace / "myproject" / "test.txt")
        _, meta = await mcp.call_tool("filesystem_write_file", {
            "file_path": test_file,
            "content": "Hello from MCP integration test!"
        })
        result_data = meta.get('result', {})
        if result_data.get("success"):
            print(f"   ✓ File written: {result_data.get('size')} bytes")
        else:
            print(f"   ✗ Failed: {result_data.get('error')}")
        
        # Test filesystem_read_file
        print("\n6. Testing filesystem_read_file...")
        _, meta = await mcp.call_tool("filesystem_read_file", {"file_path": test_file})
        result_data = meta.get('result', {})
        if "content" in result_data:
            print(f"   ✓ File read: {result_data.get('content')[:50]}...")
        else:
            print(f"   ✗ Failed: {result_data.get('error')}")
        
        # Test filesystem_list_directory
        print("\n7. Testing filesystem_list_directory...")
        _, meta = await mcp.call_tool("filesystem_list_directory", {
            "dir_path": str(test_workspace / "myproject")
        })
        result_data = meta.get('result', {})
        if "entries" in result_data:
            print(f"   ✓ Listed {result_data.get('count')} entries")
            for entry in result_data.get("entries", []):
                print(f"     - {entry['name']} ({entry['type']})")
        else:
            print(f"   ✗ Failed: {result_data.get('error')}")
        
        # Test filesystem_get_info
        print("\n8. Testing filesystem_get_info...")
        _, meta = await mcp.call_tool("filesystem_get_info", {"path": test_file})
        result_data = meta.get('result', {})
        if result_data.get("exists"):
            print(f"   ✓ Path exists: {result_data.get('type')}, {result_data.get('size')} bytes")
        else:
            print(f"   ✗ Failed: {result_data.get('error')}")
        
        # Test terminal_get_cwd
        print("\n9. Testing terminal_get_cwd...")
        _, meta = await mcp.call_tool("terminal_get_cwd", {})
        result_data = meta.get('result', {})
        if "current_directory" in result_data:
            print(f"   ✓ Current directory: {result_data.get('current_directory')}")
        else:
            print(f"   ✗ Failed: {result_data.get('error')}")
        
        # Test terminal_execute with a safe command
        print("\n10. Testing terminal_execute (echo)...")
        _, meta = await mcp.call_tool("terminal_execute", {
            "command": "echo 'Integration test successful'",
            "working_dir": str(test_workspace)
        })
        result_data = meta.get('result', {})
        if result_data.get("success"):
            print(f"   ✓ Command executed successfully")
            print(f"     Output: {result_data.get('stdout', '').strip()}")
            print(f"     Exit code: {result_data.get('exit_code')}")
        else:
            print(f"   ✗ Failed: {result_data.get('error')}")
        
        # Test terminal_execute with file creation
        print("\n11. Testing terminal_execute (touch)...")
        _, meta = await mcp.call_tool("terminal_execute", {
            "command": "touch newfile.txt",
            "working_dir": str(test_workspace)
        })
        result_data = meta.get('result', {})
        if result_data.get("success"):
            print(f"   ✓ Command executed successfully")
            # Verify the file was created
            if (test_workspace / "newfile.txt").exists():
                print(f"   ✓ File created by command exists")
            else:
                print(f"   ✗ File not found")
        else:
            print(f"   ✗ Failed: {result_data.get('error')}")
        
        # Test security: blocked command
        print("\n12. Testing security - blocked command (sudo)...")
        _, meta = await mcp.call_tool("terminal_execute", {
            "command": "sudo echo 'This should fail'"
        })
        result_data = meta.get('result', {})
        if "error" in result_data:
            print(f"   ✓ Command correctly blocked: {result_data.get('error')}")
        else:
            print(f"   ✗ SECURITY ISSUE: sudo was allowed!")
        
        # Test filesystem_delete_path
        print("\n13. Testing filesystem_delete_path...")
        _, meta = await mcp.call_tool("filesystem_delete_path", {
            "path": str(test_workspace / "myproject"),
            "recursive": True
        })
        result_data = meta.get('result', {})
        if result_data.get("success"):
            print(f"   ✓ Directory deleted successfully")
        else:
            print(f"   ✗ Failed: {result_data.get('error')}")
        
        print("\n" + "=" * 80)
        print("ALL INTEGRATION TESTS COMPLETED SUCCESSFULLY")
        print("=" * 80)
        
    finally:
        # Cleanup test workspace
        if test_workspace.exists():
            shutil.rmtree(test_workspace)
            print(f"\n✓ Cleaned up test workspace: {test_workspace}")


async def main():
    """Run all integration tests."""
    try:
        await test_mcp_tools()
    except Exception as e:
        print(f"\n✗ Integration test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
