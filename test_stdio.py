#!/usr/bin/env python3
"""
Test script to verify stdio transport compatibility
"""
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Test if server can run in stdio mode
def test_stdio_transport():
    from mcp.server.fastmcp import FastMCP
    
    # Create a minimal server
    test_server = FastMCP("TestServer")
    
    @test_server.tool()
    def echo(message: str) -> dict:
        """Echo a message"""
        return {"message": message}
    
    print("Testing stdio transport compatibility...", file=sys.stderr)
    
    # Check if stdio transport is available
    import inspect
    sig = inspect.signature(test_server.run)
    params = sig.parameters
    
    if 'transport' in params:
        annotation = params['transport'].annotation
        print(f"Transport parameter found: {annotation}", file=sys.stderr)
        
        # Check if stdio is in the Literal options
        if 'stdio' in str(annotation):
            print("✓ stdio transport is supported", file=sys.stderr)
            return True
        else:
            print("✗ stdio transport not found in options", file=sys.stderr)
            return False
    else:
        print("✗ No transport parameter found", file=sys.stderr)
        return False

if __name__ == "__main__":
    result = test_stdio_transport()
    sys.exit(0 if result else 1)
