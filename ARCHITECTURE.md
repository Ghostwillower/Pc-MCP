# Architecture Design

## Overview

The CadSlicerPrinter MCP Server has been redesigned around the OpenAI MCP framework for maximum backend efficiency while maintaining all features. This document describes the new modular architecture.

## Design Principles

1. **Separation of Concerns**: Each module has a single, well-defined responsibility
2. **Performance First**: Async operations, connection pooling, and caching throughout
3. **Maintainability**: Clear module boundaries with minimal coupling
4. **Scalability**: Easy to add new tools, services, or transports
5. **Zero Feature Loss**: All existing functionality preserved

## Directory Structure

```
src/
├── server.py              # Main entry point (381 lines, down from 1461)
├── config/                # Configuration management
│   ├── __init__.py
│   └── settings.py        # Centralized settings with validation
├── services/              # Business logic layer
│   ├── __init__.py
│   ├── cad_service.py     # CAD model operations
│   ├── slicer_service.py  # G-code slicing operations
│   ├── printer_service.py # OctoPrint integration
│   └── workspace_service.py # Workspace management
├── tools/                 # MCP tool definitions
│   ├── __init__.py
│   ├── cad_tools.py       # CAD-related MCP tools
│   ├── slicer_tools.py    # Slicing-related MCP tools
│   ├── printer_tools.py   # Printer-related MCP tools
│   └── workspace_tools.py # Workspace-related MCP tools
├── utils/                 # Shared utilities
│   ├── __init__.py
│   ├── validation.py      # Input validation
│   ├── command.py         # Command execution (sync & async)
│   └── paths.py           # Path management with caching
└── static/                # Web UI assets
```

## Module Responsibilities

### Configuration (`config/`)

**Purpose**: Centralized configuration management

**Key Features**:
- Single source of truth for all settings
- Environment variable loading with validation
- @lru_cache for efficient settings access
- Clear validation messages at startup

**Example**:
```python
from config import get_settings

settings = get_settings()  # Cached, only created once
print(settings.workspace_dir)
```

### Services (`services/`)

**Purpose**: Business logic for core operations

Each service encapsulates a specific domain:

- **CADService**: Model creation, parameter updates, preview rendering
- **SlicerService**: STL generation, G-code slicing
- **PrinterService**: OctoPrint API with async HTTP and connection pooling
- **WorkspaceService**: Model listing and workspace management

**Key Features**:
- Async operations for I/O-bound tasks
- Connection pooling for external APIs (httpx.AsyncClient)
- Consistent error handling
- No direct MCP dependency (testable in isolation)

**Example**:
```python
from services import CADService

cad = CADService()
result = await cad.render_preview("model123")
```

### Tools (`tools/`)

**Purpose**: MCP tool registration and documentation

**Key Features**:
- Thin wrappers around service methods
- Rich documentation for AI assistants
- Type hints for better IDE support
- Separated by domain for clarity

**Example**:
```python
from tools import register_cad_tools

register_cad_tools(mcp, cad_service)
```

### Utilities (`utils/`)

**Purpose**: Shared helper functions

**Key Features**:
- **validation.py**: Input sanitization (prevent directory traversal)
- **command.py**: Both sync and async command execution
- **paths.py**: @lru_cache for model directory lookups

**Example**:
```python
from utils import get_model_dir, run_command_async

model_path = get_model_dir("model123")  # Cached
result = await run_command_async(["openscad", ...])
```

## Performance Optimizations

### 1. Async Operations

All I/O-bound operations are now async:
- File I/O for previews and slicing
- HTTP requests to OctoPrint
- External process execution (OpenSCAD, slicers)

**Before**:
```python
def render_preview(...):
    subprocess.run(["openscad", ...])  # Blocks
```

**After**:
```python
async def render_preview(...):
    await run_command_async(["openscad", ...])  # Non-blocking
```

### 2. Connection Pooling

OctoPrint API calls now use httpx.AsyncClient with connection pooling:

**Before** (requests library):
```python
requests.get(url)  # New connection each time
```

**After** (httpx with pooling):
```python
client = await self._get_client()  # Reused connection
await client.get(url)
```

### 3. Caching

Frequently accessed data is cached:

```python
@lru_cache()
def get_settings():
    return Settings()  # Created once, reused

@lru_cache(maxsize=128)
def get_model_dir(model_id: str):
    return settings.models_dir / sanitize_model_id(model_id)
```

### 4. Lazy Loading

Optional dependencies loaded only when needed:

```python
try:
    from starlette import ...
    WEB_DEPENDENCIES_AVAILABLE = True
except ImportError:
    WEB_DEPENDENCIES_AVAILABLE = False
```

## Benefits

### Maintainability

- **74% reduction** in server.py size (1461 → 381 lines)
- Clear module boundaries
- Easy to test individual components
- Simple to add new features

### Performance

- **Async operations** don't block event loop
- **Connection pooling** reduces HTTP overhead
- **Caching** eliminates redundant operations
- **Configurable timeouts** prevent resource locks

### Reliability

- Centralized configuration validation
- Consistent error handling across services
- Input validation at entry points
- Clear separation of concerns

## Migration Guide

### For Users

No changes required! All existing:
- Environment variables work the same
- Command-line arguments unchanged
- Tools have identical signatures
- Web interface remains functional

### For Developers

If extending the server:

1. **Add a new tool**:
   - Create service method in appropriate service class
   - Register tool in corresponding tools file
   - Service is automatically available to tool

2. **Add a new service**:
   - Create service class in `services/`
   - Create tool registration in `tools/`
   - Import in server.py

3. **Add configuration**:
   - Add to `Settings` class in `config/settings.py`
   - Configuration automatically validated and cached

## Testing Strategy

The modular design enables comprehensive testing:

1. **Unit Tests**: Test services in isolation
2. **Integration Tests**: Test MCP protocol compliance
3. **Performance Tests**: Benchmark async operations
4. **Regression Tests**: Ensure feature parity

## Future Enhancements

The new architecture enables:

- **Background task queue** for long-running operations
- **Result caching** for expensive computations
- **MCP resources** for model state
- **MCP prompts** for workflow automation
- **Metrics and monitoring** hooks
- **Plugin system** for extensibility

## Conclusion

The redesigned architecture delivers:
- ✅ **Maximum backend efficiency** through async operations and caching
- ✅ **No feature loss** - 100% backward compatible
- ✅ **Better maintainability** with clear separation of concerns
- ✅ **Future-proof design** ready for enhancements
- ✅ **OpenAI MCP compliance** with proper framework usage
