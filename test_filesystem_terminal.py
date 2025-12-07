#!/usr/bin/env python3
"""Test filesystem and terminal functionality."""

import sys
import asyncio
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from services.filesystem_service import FilesystemService
from services.terminal_service import TerminalService


def test_filesystem_service():
    """Test filesystem service operations."""
    print("=" * 80)
    print("Testing Filesystem Service")
    print("=" * 80)
    
    fs = FilesystemService()
    
    # Test 1: List directory
    print("\n1. List current directory:")
    result = fs.list_directory(".", show_hidden=False, recursive=False)
    print(f"   Found {result.get('count', 0)} entries")
    if 'entries' in result:
        for entry in result['entries'][:5]:  # Show first 5
            print(f"   - {entry['name']} ({entry['type']})")
    
    # Test 2: Create test directory
    print("\n2. Create test directory:")
    test_dir = "./workspace/test_filesystem"
    result = fs.create_directory(test_dir)
    print(f"   {result.get('message', result.get('error', 'Unknown'))}")
    
    # Test 3: Write test file
    print("\n3. Write test file:")
    test_file = f"{test_dir}/test.txt"
    result = fs.write_file(test_file, "Hello from filesystem test!")
    print(f"   {result.get('message', result.get('error', 'Unknown'))}")
    
    # Test 4: Read test file
    print("\n4. Read test file:")
    result = fs.read_file(test_file)
    if 'content' in result:
        print(f"   Content: {result['content']}")
        print(f"   Size: {result['size']} bytes")
    else:
        print(f"   Error: {result.get('error')}")
    
    # Test 5: Get file info
    print("\n5. Get file info:")
    result = fs.get_path_info(test_file)
    if 'exists' in result and result['exists']:
        print(f"   Path: {result['path']}")
        print(f"   Type: {result['type']}")
        print(f"   Size: {result['size']} bytes")
    else:
        print(f"   Error: {result.get('error')}")
    
    # Test 6: Attempt to access restricted path (should fail)
    print("\n6. Test security - attempt to access /etc/passwd:")
    result = fs.read_file("/etc/passwd")
    if 'error' in result:
        print(f"   ✓ Correctly blocked: {result['error']}")
    else:
        print(f"   ✗ SECURITY ISSUE: Access was allowed!")
    
    # Cleanup
    print("\n7. Cleanup:")
    result = fs.delete_path(test_dir, recursive=True)
    print(f"   {result.get('message', result.get('error', 'Unknown'))}")
    
    print("\n" + "=" * 80)


async def test_terminal_service():
    """Test terminal service operations."""
    print("=" * 80)
    print("Testing Terminal Service")
    print("=" * 80)
    
    term = TerminalService()
    
    # Test 1: Execute safe command
    print("\n1. Execute 'echo Hello World':")
    result = await term.execute_command("echo 'Hello World'")
    if result.get('success'):
        print(f"   ✓ Success")
        print(f"   Output: {result['stdout'].strip()}")
        print(f"   Exit code: {result['exit_code']}")
    else:
        print(f"   Error: {result.get('error', 'Unknown')}")
    
    # Test 2: Execute another safe command
    print("\n2. Execute 'pwd':")
    result = await term.execute_command("pwd")
    if result.get('success'):
        print(f"   ✓ Success")
        print(f"   Working directory: {result['stdout'].strip()}")
    else:
        print(f"   Error: {result.get('error', 'Unknown')}")
    
    # Test 3: Get current directory
    print("\n3. Get current directory:")
    result = term.get_current_directory()
    print(f"   Current directory: {result.get('current_directory')}")
    print(f"   Is allowed: {result.get('is_allowed')}")
    
    # Test 4: Get environment variables
    print("\n4. Get environment variables:")
    result = term.get_environment_variables()
    count = result.get('count', 0)
    print(f"   Found {count} environment variables")
    env_vars = result.get('environment_variables', {})
    # Show a few safe ones
    for key in ['PATH', 'HOME', 'USER'][:3]:
        if key in env_vars:
            value = env_vars[key]
            if len(value) > 50:
                value = value[:50] + "..."
            print(f"   {key}: {value}")
    
    # Test 5: Attempt to execute blocked command (should fail)
    print("\n5. Test security - attempt to execute 'sudo ls':")
    result = await term.execute_command("sudo ls")
    if 'error' in result:
        print(f"   ✓ Correctly blocked: {result['error']}")
    else:
        print(f"   ✗ SECURITY ISSUE: sudo was allowed!")
    
    # Test 6: Another blocked command
    print("\n6. Test security - attempt to execute 'systemctl status':")
    result = await term.execute_command("systemctl status")
    if 'error' in result:
        print(f"   ✓ Correctly blocked: {result['error']}")
    else:
        print(f"   ✗ SECURITY ISSUE: systemctl was allowed!")
    
    print("\n" + "=" * 80)


async def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "FILESYSTEM AND TERMINAL TESTS" + " " * 29 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    # Test filesystem
    test_filesystem_service()
    
    print()
    
    # Test terminal
    await test_terminal_service()
    
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 30 + "ALL TESTS COMPLETE" + " " * 30 + "║")
    print("╚" + "=" * 78 + "╝")
    print()


if __name__ == "__main__":
    asyncio.run(main())
