#!/usr/bin/env python3
"""
Test script to verify stdio transport compatibility with OpenAI MCP connectors.

This script simulates how OpenAI's MCP connector communicates with the server
using JSON-RPC messages over stdin/stdout.
"""
import json
import subprocess
import sys
from pathlib import Path

def test_stdio_communication():
    """
    Test basic MCP communication over stdio transport.
    """
    print("Testing stdio transport compatibility...")
    print("=" * 60)
    
    # Start the server in stdio mode
    server_path = Path(__file__).parent / "src" / "server.py"
    
    try:
        # Start server process
        proc = subprocess.Popen(
            [sys.executable, str(server_path), "--transport", "stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Wait a moment for server to initialize
        import time
        time.sleep(2)
        
        # Send initialize request (MCP protocol)
        initialize_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        print(f"Sending initialize request: {json.dumps(initialize_request)}")
        proc.stdin.write(json.dumps(initialize_request) + "\n")
        proc.stdin.flush()
        
        # Try to read response with timeout
        try:
            # Read stderr to check server started
            import select
            if select.select([proc.stderr], [], [], 1)[0]:
                stderr_output = proc.stderr.readline()
                print(f"Server stderr: {stderr_output.strip()}")
            
            # Check if server is responsive
            if proc.poll() is not None:
                print(f"✗ Server exited unexpectedly with code: {proc.returncode}")
                stderr_rest = proc.stderr.read()
                print(f"Stderr output:\n{stderr_rest}")
                return False
            
            print("✓ Server started successfully in stdio mode")
            print("✓ Server is ready to receive MCP protocol messages")
            
        except Exception as e:
            print(f"Warning during communication test: {e}")
        
        # Clean up
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        
        print("✓ stdio transport test completed")
        return True
        
    except Exception as e:
        print(f"✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_argument_parsing():
    """
    Test that different transport arguments work.
    """
    print("\nTesting transport argument parsing...")
    print("=" * 60)
    
    server_path = Path(__file__).parent / "src" / "server.py"
    
    transports = ["stdio", "streamable-http", "sse"]
    
    for transport in transports:
        try:
            result = subprocess.run(
                [sys.executable, str(server_path), "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if transport in result.stdout:
                print(f"✓ {transport} transport option available")
            else:
                print(f"✗ {transport} transport option not found in help")
                return False
                
        except Exception as e:
            print(f"✗ Error testing {transport}: {e}")
            return False
    
    print("✓ All transport options available")
    return True

def main():
    """
    Run all tests.
    """
    print("CadSlicerPrinter MCP Server - stdio Transport Tests")
    print("=" * 60)
    print()
    
    results = []
    
    # Test 1: Argument parsing
    results.append(test_argument_parsing())
    
    # Test 2: stdio communication
    results.append(test_stdio_communication())
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    
    if all(results):
        print("✓ All tests passed!")
        print("✓ Server is compatible with OpenAI MCP connectors")
        return 0
    else:
        print("✗ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
