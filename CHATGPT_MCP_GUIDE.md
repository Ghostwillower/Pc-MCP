# Building MCP Servers for ChatGPT and API Integrations

A comprehensive guide to building Model Context Protocol (MCP) servers that work with ChatGPT connectors, deep research, and API integrations.

## Table of Contents

1. [Introduction](#introduction)
2. [Understanding MCP](#understanding-mcp)
3. [Prerequisites](#prerequisites)
4. [Data Source Configuration](#data-source-configuration)
5. [Building Your MCP Server](#building-your-mcp-server)
6. [Required Tools: Search and Fetch](#required-tools-search-and-fetch)
7. [Complete Server Implementation](#complete-server-implementation)
8. [Deployment Options](#deployment-options)
9. [Testing and Connection](#testing-and-connection)
10. [Authentication and Security](#authentication-and-security)
11. [ChatGPT Integration](#chatgpt-integration)
12. [Risks and Safety Considerations](#risks-and-safety-considerations)
13. [Best Practices](#best-practices)
14. [Troubleshooting](#troubleshooting)

## Introduction

[Model Context Protocol](https://modelcontextprotocol.io/introduction) (MCP) is an open protocol that's becoming the industry standard for extending AI models with additional tools and knowledge. Remote MCP servers can be used to connect models over the Internet to new data sources and capabilities.

This guide covers how to build a remote MCP server that reads data from a private data source (such as a [vector store](/docs/guides/retrieval)) and makes it available in ChatGPT via:
- Connectors in chat and deep research
- API integrations via the [Responses API](/docs/guides/deep-research)

**Note**: You can build and use full MCP connectors with the **developer mode** beta. Pro and Plus users can enable it under **Settings → Connectors → Advanced → Developer mode** to access the complete set of MCP tools. Learn more in the [Developer mode guide](/docs/guides/developer-mode).

## Understanding MCP

### What is MCP?

The Model Context Protocol (MCP) provides a standardized way to:
- Extend AI models with custom tools and data sources
- Create reusable integrations across different AI platforms
- Build secure connections between AI models and external systems

### Why Build an MCP Server?

- **Data Integration**: Connect ChatGPT to your private data sources
- **Custom Tools**: Provide specialized functionality to AI models
- **API Access**: Use deep research features programmatically
- **Scalability**: Build once, use across multiple platforms

### Key Components

1. **Server**: Your implementation that provides tools and data
2. **Transport**: Communication protocol (SSE, stdio, HTTP)
3. **Tools**: Functions that ChatGPT can call (`search` and `fetch`)
4. **Client**: ChatGPT or API integration consuming your server

## Prerequisites

### Required Knowledge

- Basic Python programming (or your chosen language)
- Understanding of REST APIs
- Familiarity with async programming (for Python implementations)

### Required Tools

- Python 3.10 or higher (for FastMCP examples)
- OpenAI API key
- Access to a data source (vector store, database, etc.)
- Development environment (local or Replit)

### Required Libraries

For Python with FastMCP:
```bash
pip install fastmcp openai httpx
```

## Data Source Configuration

Before building your MCP server, you need a data source. This guide uses OpenAI's vector stores, but you can use any data source.

### Using OpenAI Vector Stores

#### Step 1: Upload Documents

You can upload files and create a vector store in the [dashboard](https://platform.openai.com/storage/vector_stores) or via API.

Example using the API:
```python
from openai import OpenAI

client = OpenAI()

# Create a vector store
vector_store = client.vector_stores.create(
    name="My Knowledge Base"
)

# Upload a file
with open("document.pdf", "rb") as file:
    file_obj = client.files.create(
        file=file,
        purpose="assistants"
    )
    
    # Add file to vector store
    client.vector_stores.files.create(
        vector_store_id=vector_store.id,
        file_id=file_obj.id
    )

print(f"Vector Store ID: {vector_store.id}")
```

#### Step 2: Note Your Vector Store ID

Save the vector store ID - you'll need it for your MCP server configuration.

Example: `vs_abc123xyz...`

![Vector Store Configuration](https://cdn.openai.com/API/docs/images/vector_store.png)

### Alternative Data Sources

Your MCP server can work with any data source:
- Traditional databases (PostgreSQL, MongoDB, etc.)
- Search engines (Elasticsearch, Algolia)
- File systems
- APIs and web services
- Custom data structures

The key is implementing the required `search` and `fetch` tools to interface with your chosen data source.

## Building Your MCP Server

### Choosing a Framework

There are several MCP server frameworks available:

**Python:**
- [FastMCP](https://github.com/jlowin/fastmcp) - Simple, async-first framework
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) - Official SDK

**TypeScript/JavaScript:**
- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)

**Other Languages:**
- Go, Rust, and other implementations available in the MCP ecosystem

This guide focuses on FastMCP for simplicity and performance.

### Project Structure

Create a clean project structure:

```
my-mcp-server/
├── server.py          # Main server implementation
├── requirements.txt   # Python dependencies
├── .env              # Environment variables
└── README.md         # Documentation
```

### Basic Server Setup

Create `requirements.txt`:
```txt
fastmcp>=1.0.0
openai>=1.0.0
httpx>=0.27.0
python-dotenv>=1.0.0
```

Create `.env`:
```env
OPENAI_API_KEY=your_api_key_here
VECTOR_STORE_ID=vs_your_vector_store_id
```

## Required Tools: Search and Fetch

To work with ChatGPT Connectors or deep research (in ChatGPT or via API), your MCP server **must** implement two tools: `search` and `fetch`.

### The `search` Tool

The `search` tool returns a list of relevant search results from your data source.

#### Arguments

- `query` (string): The search query from the user

#### Returns

An object with a single key `results`, containing an array of result objects. Each result must include:

- `id` (string): Unique identifier for the document/item
- `title` (string): Human-readable title
- `url` (string): Canonical URL for citation

#### Response Format

In MCP, tool results must be returned as [a content array](https://modelcontextprotocol.io/docs/learn/architecture#understanding-the-tool-execution-response). The `search` tool must return **exactly one** content item with:

- `type: "text"`
- `text`: JSON-encoded string matching the results schema

Example response:
```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"results\":[{\"id\":\"doc-1\",\"title\":\"Example Document\",\"url\":\"https://example.com/doc-1\"},{\"id\":\"doc-2\",\"title\":\"Another Document\",\"url\":\"https://example.com/doc-2\"}]}"
    }
  ]
}
```

#### Implementation Example

```python
@mcp.tool()
async def search(query: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Search for documents based on a query.
    
    Args:
        query: Search query string
        
    Returns:
        Dictionary with 'results' key containing matching documents
    """
    if not query or not query.strip():
        return {"results": []}
    
    # Search your data source
    response = openai_client.vector_stores.search(
        vector_store_id=VECTOR_STORE_ID,
        query=query
    )
    
    results = []
    if hasattr(response, 'data') and response.data:
        for i, item in enumerate(response.data):
            result = {
                "id": getattr(item, 'file_id', f"doc_{i}"),
                "title": getattr(item, 'filename', f"Document {i+1}"),
                "url": f"https://platform.openai.com/storage/files/{item.file_id}"
            }
            results.append(result)
    
    return {"results": results}
```

### The `fetch` Tool

The `fetch` tool retrieves complete document content by ID.

#### Arguments

- `id` (string): Unique identifier for the document (from search results)

#### Returns

A single object with the following properties:

- `id` (string): Unique identifier
- `title` (string): Document title
- `text` (string): Full text content
- `url` (string): URL for citation
- `metadata` (object, optional): Additional metadata about the document

#### Response Format

The `fetch` tool must return exactly [one content item with `type: "text"`](https://modelcontextprotocol.io/specification/2025-06-18/server/tools#tool-result). The `text` field should be a JSON-encoded string following the schema above.

Example response:
```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"id\":\"doc-1\",\"title\":\"Example Document\",\"text\":\"This is the full content of the document...\",\"url\":\"https://example.com/doc-1\",\"metadata\":{\"source\":\"vector_store\",\"created\":\"2024-01-01\"}}"
    }
  ]
}
```

#### Implementation Example

```python
@mcp.tool()
async def fetch(id: str) -> Dict[str, Any]:
    """
    Retrieve complete document content by ID.
    
    Args:
        id: Document identifier from search results
        
    Returns:
        Complete document with id, title, text, url, and metadata
    """
    if not id:
        raise ValueError("Document ID is required")
    
    # Fetch file content
    content_response = openai_client.vector_stores.files.content(
        vector_store_id=VECTOR_STORE_ID,
        file_id=id
    )
    
    # Get file metadata
    file_info = openai_client.vector_stores.files.retrieve(
        vector_store_id=VECTOR_STORE_ID,
        file_id=id
    )
    
    # Extract text content
    file_content = ""
    if hasattr(content_response, 'data') and content_response.data:
        content_parts = [
            content_item.text 
            for content_item in content_response.data 
            if hasattr(content_item, 'text')
        ]
        file_content = "\n".join(content_parts)
    
    result = {
        "id": id,
        "title": getattr(file_info, 'filename', f"Document {id}"),
        "text": file_content or "No content available",
        "url": f"https://platform.openai.com/storage/files/{id}",
        "metadata": getattr(file_info, 'attributes', None)
    }
    
    return result
```

## Complete Server Implementation

Here's a full, production-ready MCP server implementation using FastMCP:

```python
"""
Sample MCP Server for ChatGPT Integration

This server implements the Model Context Protocol (MCP) with search and fetch
capabilities designed to work with ChatGPT's chat and deep research features.
"""

import logging
import os
from typing import Dict, List, Any

from fastmcp import FastMCP
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAI configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
VECTOR_STORE_ID = os.environ.get("VECTOR_STORE_ID", "")

# Initialize OpenAI client
openai_client = OpenAI()

server_instructions = """
This MCP server provides search and document retrieval capabilities
for chat and deep research connectors. Use the search tool to find relevant documents
based on keywords, then use the fetch tool to retrieve complete
document content with citations.
"""

def create_server():
    """Create and configure the MCP server with search and fetch tools."""

    # Initialize the FastMCP server
    mcp = FastMCP(name="Sample MCP Server",
                  instructions=server_instructions)

    @mcp.tool()
    async def search(query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search for documents using OpenAI Vector Store search.

        This tool searches through the vector store to find semantically relevant matches.
        Returns a list of search results with basic information. Use the fetch tool to get
        complete document content.

        Args:
            query: Search query string. Natural language queries work best for semantic search.

        Returns:
            Dictionary with 'results' key containing list of matching documents.
            Each result includes id, title, text snippet, and optional URL.
        """
        if not query or not query.strip():
            return {"results": []}

        if not openai_client:
            logger.error("OpenAI client not initialized - API key missing")
            raise ValueError(
                "OpenAI API key is required for vector store search")

        # Search the vector store using OpenAI API
        logger.info(f"Searching {VECTOR_STORE_ID} for query: '{query}'")

        response = openai_client.vector_stores.search(
            vector_store_id=VECTOR_STORE_ID, query=query)

        results = []

        # Process the vector store search results
        if hasattr(response, 'data') and response.data:
            for i, item in enumerate(response.data):
                # Extract file_id, filename, and content
                item_id = getattr(item, 'file_id', f"vs_{i}")
                item_filename = getattr(item, 'filename', f"Document {i+1}")

                # Extract text content from the content array
                content_list = getattr(item, 'content', [])
                text_content = ""
                if content_list and len(content_list) > 0:
                    # Get text from the first content item
                    first_content = content_list[0]
                    if hasattr(first_content, 'text'):
                        text_content = first_content.text
                    elif isinstance(first_content, dict):
                        text_content = first_content.get('text', '')

                if not text_content:
                    text_content = "No content available"

                # Create a snippet from content
                text_snippet = text_content[:200] + "..." if len(
                    text_content) > 200 else text_content

                result = {
                    "id": item_id,
                    "title": item_filename,
                    "text": text_snippet,
                    "url":
                    f"https://platform.openai.com/storage/files/{item_id}"
                }

                results.append(result)

        logger.info(f"Vector store search returned {len(results)} results")
        return {"results": results}

    @mcp.tool()
    async def fetch(id: str) -> Dict[str, Any]:
        """
        Retrieve complete document content by ID for detailed
        analysis and citation. This tool fetches the full document
        content from OpenAI Vector Store. Use this after finding
        relevant documents with the search tool to get complete
        information for analysis and proper citation.

        Args:
            id: File ID from vector store (file-xxx) or local document ID

        Returns:
            Complete document with id, title, full text content,
            optional URL, and metadata

        Raises:
            ValueError: If the specified ID is not found
        """
        if not id:
            raise ValueError("Document ID is required")

        if not openai_client:
            logger.error("OpenAI client not initialized - API key missing")
            raise ValueError(
                "OpenAI API key is required for vector store file retrieval")

        logger.info(f"Fetching content from vector store for file ID: {id}")

        # Fetch file content from vector store
        content_response = openai_client.vector_stores.files.content(
            vector_store_id=VECTOR_STORE_ID, file_id=id)

        # Get file metadata
        file_info = openai_client.vector_stores.files.retrieve(
            vector_store_id=VECTOR_STORE_ID, file_id=id)

        # Extract content from paginated response
        file_content = ""
        if hasattr(content_response, 'data') and content_response.data:
            # Combine all content chunks from FileContentResponse objects
            content_parts = []
            for content_item in content_response.data:
                if hasattr(content_item, 'text'):
                    content_parts.append(content_item.text)
            file_content = "\n".join(content_parts)
        else:
            file_content = "No content available"

        # Use filename as title and create proper URL for citations
        filename = getattr(file_info, 'filename', f"Document {id}")

        result = {
            "id": id,
            "title": filename,
            "text": file_content,
            "url": f"https://platform.openai.com/storage/files/{id}",
            "metadata": None
        }

        # Add metadata if available from file info
        if hasattr(file_info, 'attributes') and file_info.attributes:
            result["metadata"] = file_info.attributes

        logger.info(f"Fetched vector store file: {id}")
        return result

    return mcp

def main():
    """Main function to start the MCP server."""
    # Verify OpenAI client is initialized
    if not openai_client:
        logger.error(
            "OpenAI API key not found. Please set OPENAI_API_KEY environment variable."
        )
        raise ValueError("OpenAI API key is required")

    logger.info(f"Using vector store: {VECTOR_STORE_ID}")

    # Create the MCP server
    server = create_server()

    # Configure and start the server
    logger.info("Starting MCP server on 0.0.0.0:8000")
    logger.info("Server will be accessible via SSE transport")

    try:
        # Use FastMCP's built-in run method with SSE transport
        server.run(transport="sse", host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

if __name__ == "__main__":
    main()
```

### Key Implementation Details

1. **Async Operations**: Both tools use `async` for non-blocking I/O
2. **Error Handling**: Comprehensive validation and error messages
3. **Logging**: Detailed logging for debugging and monitoring
4. **Type Hints**: Clear parameter and return types
5. **Documentation**: Rich docstrings for AI understanding

## Deployment Options

### Option 1: Replit (Quick Start)

Replit provides the fastest way to test your MCP server:

#### Step 1: Create a Replit Project

1. Go to [Replit](https://replit.com/)
2. Create a new Python repl
3. Copy your server code to `main.py`

#### Step 2: Configure Secrets

In the Replit "Secrets" UI (lock icon), add:
- `OPENAI_API_KEY`: Your OpenAI API key
- `VECTOR_STORE_ID`: Your vector store ID

#### Step 3: Install Dependencies

Create `requirements.txt`:
```txt
fastmcp>=1.0.0
openai>=1.0.0
```

Replit will automatically install dependencies.

#### Step 4: Get Your Server URL

1. Run your server
2. Click the chainlink icon to get the public URL
3. Ensure the URL ends with `/sse/`

Example URL: `https://777xxx.janeway.replit.dev/sse/`

**Important**: On free Replit accounts, keep the editor tab open while testing to keep the server active.

[View Example on Replit](https://replit.com/@kwhinnery-oai/DeepResearchServer?v=1#README.md)

### Option 2: Local Development

#### Step 1: Set Up Environment

```bash
# Create project directory
mkdir my-mcp-server
cd my-mcp-server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastmcp openai httpx python-dotenv
```

#### Step 2: Configure Environment

Create `.env`:
```env
OPENAI_API_KEY=your_api_key_here
VECTOR_STORE_ID=vs_your_vector_store_id
```

#### Step 3: Run the Server

```bash
python server.py
```

The server will be available at `http://localhost:8000/sse/`

### Option 3: Cloud Deployment

For production deployments, consider:

**Platform as a Service (PaaS):**
- Heroku
- Railway
- Render
- Google Cloud Run
- AWS App Runner

**Containerized Deployment:**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

EXPOSE 8000

CMD ["python", "server.py"]
```

**Environment Variables:**
Ensure your deployment platform has access to:
- `OPENAI_API_KEY`
- `VECTOR_STORE_ID`

## Testing and Connection

### Testing via Prompts Dashboard

1. Navigate to the [Prompts Dashboard](https://platform.openai.com/chat)
2. Create a new prompt or edit an existing one
3. Add a new MCP tool to the prompt configuration
4. Enter your server URL (e.g., `https://your-server.dev/sse/`)
5. Set "Require Approval" to "Never" for API usage

![Prompts Configuration](https://cdn.openai.com/API/docs/images/prompts_mcp.png)

### Testing via Chat Interface

Once configured, test your server:

```
User: Search for information about cats
→ Server search tool is called
→ Results are returned

User: Tell me more about the first result
→ Server fetch tool is called
→ Full content is retrieved
```

![Prompts Chat](https://cdn.openai.com/API/docs/images/chat_prompts_mcp.png)

### Testing via API

Use the Responses API to test programmatically:

```bash
curl https://api.openai.com/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
  "model": "o4-mini-deep-research",
  "input": [
    {
      "role": "developer",
      "content": [
        {
          "type": "input_text",
          "text": "You are a research assistant that searches MCP servers to find answers to your questions."
        }
      ]
    },
    {
      "role": "user",
      "content": [
        {
          "type": "input_text",
          "text": "What information do you have about machine learning?"
        }
      ]
    }
  ],
  "reasoning": {
    "summary": "auto"
  },
  "tools": [
    {
      "type": "mcp",
      "server_label": "my-knowledge-base",
      "server_url": "https://your-server.dev/sse/",
      "allowed_tools": [
        "search",
        "fetch"
      ],
      "require_approval": "never"
    }
  ]
}'
```

### Verifying Tool Calls

Check your server logs to verify:
1. Connection established successfully
2. `search` tool called with correct query
3. Results returned in proper format
4. `fetch` tool called for specific documents
5. Full content retrieved and returned

## Authentication and Security

### OAuth Implementation

For production servers, implement OAuth 2.0 with dynamic client registration:

#### Recommended Flow

1. **Dynamic Client Registration**: Support [MCP's DCR specification](https://modelcontextprotocol.io/specification/2025-03-26/basic/authorization#2-4-dynamic-client-registration)
2. **Authorization Endpoint**: Implement standard OAuth 2.0 authorization
3. **Token Endpoint**: Issue access tokens for authenticated requests
4. **Token Validation**: Verify tokens on each request

#### Example Implementation Sketch

```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer

app = FastAPI()
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="/oauth/authorize",
    tokenUrl="/oauth/token"
)

async def verify_token(token: str = Depends(oauth2_scheme)):
    # Verify token validity
    # Return user/client information
    pass

@app.post("/mcp/tools/search")
async def search(query: str, user=Depends(verify_token)):
    # Authenticated search
    pass
```

### Security Best Practices

1. **API Key Management**
   - Never commit API keys to version control
   - Use environment variables or secret management services
   - Rotate keys regularly

2. **Input Validation**
   - Sanitize all user inputs
   - Validate query parameters
   - Limit query length and complexity

3. **Rate Limiting**
   - Implement request throttling
   - Prevent abuse and DoS attacks
   - Set reasonable usage limits

4. **HTTPS Only**
   - Always use TLS/SSL in production
   - Enforce HTTPS redirects
   - Use valid certificates

5. **Access Control**
   - Implement proper authorization
   - Scope access to necessary data only
   - Log access attempts

### ChatGPT Workspace Integration

When connecting your MCP server in ChatGPT:
- Users will see an OAuth flow to your application
- They'll authorize access to your data source
- You can control access per user/workspace

## ChatGPT Integration

### Connecting in ChatGPT Settings

1. Open [ChatGPT Settings](https://chatgpt.com/#settings)
2. Navigate to the **Connectors** tab
3. Click "Add Custom Connector" or "Add MCP Server"
4. Enter your server URL (must end with `/sse/`)
5. Configure approval settings:
   - **For testing**: "Never" require approval
   - **For production**: "Always" or "Ask" for approval

### Using in Chat

Once connected, your MCP server appears in:

**Deep Research Mode:**
- Select "Deep Research" from the model dropdown
- Add your connector as a source
- Ask research questions

**Connector Mode:**
- Select "Use Connectors" in the composer
- Choose your custom MCP server
- Interact naturally

### Using via API

Example with the Responses API:

```python
import openai

client = openai.OpenAI()

response = client.responses.create(
    model="o4-mini-deep-research",
    input=[
        {
            "role": "developer",
            "content": [{
                "type": "input_text",
                "text": "You are a helpful research assistant."
            }]
        },
        {
            "role": "user",
            "content": [{
                "type": "input_text",
                "text": "Research the latest trends in renewable energy"
            }]
        }
    ],
    tools=[
        {
            "type": "mcp",
            "server_label": "knowledge-base",
            "server_url": "https://your-server.dev/sse/",
            "allowed_tools": ["search", "fetch"],
            "require_approval": "never"
        }
    ],
    reasoning={
        "summary": "auto"
    }
)

print(response.output)
```

## Risks and Safety Considerations

### Prompt Injection Risks

Prompt injection attacks occur when malicious content tricks ChatGPT into performing unintended actions. Understanding these risks is crucial for safe MCP deployment.

#### Risk Matrix

| Scenario | Safe if MCP Developer is Trusted? | Mitigation Strategies |
|----------|-----------------------------------|----------------------|
| **Malicious data in MCP** <br> Attacker inserts prompt injection into accessible data | ❌ No - You must trust ALL content | • Don't use MCP with untrusted user input <br> • Minimize user access to MCP |
| **Excessive parameter requests** <br> MCP requests sensitive data unnecessarily | ❌ No - Developer may request data you don't want to share | • Review all parameters when sideloading <br> • Ensure no privacy overreach |
| **Cross-MCP data theft** <br> Injection from one MCP steals data from another | ❌ No - Risk exists even with trusted MCPs | • Be aware of risks <br> • Limit access to sensitive MCPs |
| **Write action exfiltration** <br> Injection exfiltrates data via write actions | ❌ No - Even trusted MCPs can be exploited | • Carefully review write actions <br> • Monitor for unexpected data |
| **Malicious MCP logging** <br> Malicious MCP logs sensitive read parameters | ⚠️ Only if developer is fully trusted | • Only use MCPs from trusted developers |
| **Harmful write actions** <br> Injection causes destructive operations | ❌ No - Attack comes from external source | • Review all write actions <br> • Limit sensitive MCP access |

### Non-Prompt Injection Risks

#### Write Action Risks

- **Increased Power**: Write actions enable both useful and potentially destructive operations
- **Manual Confirmation**: ChatGPT requires confirmation before write actions
- **Careful Review**: Always review write confirmations for sensitive data
- **Trust Requirements**: Only deploy write actions where you accept the risk of mistakes

#### Data Exposure Risks

- **Query Data**: MCP servers receive all data ChatGPT sends in queries
- **Sensitive Information**: This may include sensitive user data from earlier in the conversation
- **Logging**: Even non-malicious servers may log query data
- **Transmission Security**: Data is transmitted to your server

### Connecting to Trusted Servers

#### Best Practices

1. **Use Official Servers**: Always prefer official servers hosted by service providers
   - ✅ Good: `mcp.stripe.com` (hosted by Stripe)
   - ❌ Bad: Third-party Stripe proxy servers

2. **Verify Server Identity**: Confirm you're connecting to the correct server
   - Check domain names carefully
   - Verify SSL certificates
   - Review server documentation

3. **Review Data Handling**: Understand how servers use your data
   - Read privacy policies
   - Check data retention policies
   - Verify security practices

4. **Limit Sensitive Data**: Be cautious with what data you provide
   - Don't send unnecessary sensitive information
   - Use data scoping and filtering
   - Implement access controls

#### Building Trusted Servers

If you're building an MCP server:

1. **Never include sensitive information** in tool JSON definitions
2. **Don't store sensitive user data** from ChatGPT interactions
3. **Implement proper authentication** and authorization
4. **Use HTTPS/TLS** for all communications
5. **Document your security practices** clearly
6. **Follow data privacy regulations** (GDPR, CCPA, etc.)

### Reporting Security Issues

If you discover a malicious MCP server, report it to: **security@openai.com**

## Best Practices

### Server Design

1. **Keep Tools Simple**
   - Each tool should do one thing well
   - Avoid complex, multi-step operations in a single tool
   - Let ChatGPT orchestrate multiple tool calls

2. **Provide Rich Documentation**
   - Write detailed docstrings for each tool
   - Include examples in descriptions
   - Specify parameter constraints clearly

3. **Handle Errors Gracefully**
   - Return meaningful error messages
   - Don't expose internal system details
   - Log errors for debugging

4. **Optimize Performance**
   - Use async operations for I/O
   - Implement caching where appropriate
   - Set reasonable timeouts
   - Use connection pooling for APIs

### Data Management

1. **Efficient Search**
   - Return relevant results quickly
   - Limit result set sizes
   - Use pagination for large datasets
   - Provide snippets, not full content

2. **Complete Fetch**
   - Return full, formatted content
   - Include proper citations
   - Add useful metadata
   - Handle missing data gracefully

3. **Content Quality**
   - Return clean, well-formatted text
   - Remove noise and irrelevant data
   - Preserve important structure
   - Include source attribution

### Security

1. **Validate All Inputs**
   - Check parameter types
   - Sanitize strings
   - Validate IDs and references
   - Prevent injection attacks

2. **Limit Access**
   - Implement proper authentication
   - Use OAuth for user authorization
   - Scope access appropriately
   - Audit access logs

3. **Protect Data**
   - Use HTTPS/TLS
   - Encrypt sensitive data
   - Follow data privacy regulations
   - Implement rate limiting

### Monitoring

1. **Log Everything**
   - Record all tool calls
   - Track errors and exceptions
   - Monitor performance metrics
   - Audit security events

2. **Monitor Health**
   - Check server availability
   - Track response times
   - Monitor resource usage
   - Alert on anomalies

3. **Analyze Usage**
   - Track popular queries
   - Identify common errors
   - Measure user satisfaction
   - Optimize based on data

## Troubleshooting

### Server Won't Start

**Problem**: Server fails to start or crashes immediately

**Solutions**:
- Check all environment variables are set correctly
- Verify Python version is 3.10+
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check for port conflicts (try a different port)
- Review logs for specific error messages

### Tools Not Being Called

**Problem**: ChatGPT connects but doesn't call your tools

**Solutions**:
- Verify tool names are exactly `search` and `fetch`
- Check tool return format matches MCP specification
- Ensure tools are properly registered with `@mcp.tool()`
- Review tool docstrings - they should be descriptive
- Test tools independently before connecting

### Search Returns No Results

**Problem**: `search` tool executes but returns empty results

**Solutions**:
- Verify vector store ID is correct
- Check OpenAI API key has access to the vector store
- Ensure vector store contains indexed documents
- Test vector store search directly via OpenAI API
- Check search query formatting

### Fetch Tool Fails

**Problem**: `fetch` tool throws errors or returns incomplete data

**Solutions**:
- Validate document ID format
- Check file exists in vector store
- Verify API permissions
- Handle missing content gracefully
- Test fetch directly with known document ID

### Authentication Issues

**Problem**: OAuth flow fails or tokens are rejected

**Solutions**:
- Verify OAuth configuration matches MCP spec
- Check redirect URIs are correct
- Ensure tokens are being validated properly
- Review OAuth error messages
- Test OAuth flow independently

### Performance Problems

**Problem**: Server is slow or times out

**Solutions**:
- Implement async operations for I/O
- Add caching for frequently accessed data
- Use connection pooling for external APIs
- Optimize database queries
- Set appropriate timeouts
- Consider adding rate limiting

### Connection Drops

**Problem**: ChatGPT loses connection to server

**Solutions**:
- Check server uptime and stability
- Verify network connectivity
- Implement proper error handling
- Add connection retry logic
- Monitor server resources (CPU, memory)
- Check for SSE transport issues

## Additional Resources

### Documentation

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [MCP Specification](https://modelcontextprotocol.io/specification)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [OpenAI API Documentation](https://platform.openai.com/docs)

### Example Implementations

- [Example on Replit](https://replit.com/@kwhinnery-oai/DeepResearchServer)
- [MCP Server Examples](https://github.com/modelcontextprotocol/servers)
- [Python SDK Examples](https://github.com/modelcontextprotocol/python-sdk/tree/main/examples)

### Community

- [MCP Discord Community](https://discord.gg/modelcontextprotocol)
- [GitHub Discussions](https://github.com/modelcontextprotocol/specification/discussions)
- [Stack Overflow (mcp tag)](https://stackoverflow.com/questions/tagged/model-context-protocol)

### Tools and Libraries

- [FastMCP](https://github.com/jlowin/fastmcp) - Python MCP framework
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)

## Conclusion

Building MCP servers for ChatGPT integration requires:

1. **Understanding** the MCP protocol and requirements
2. **Implementing** the required `search` and `fetch` tools
3. **Deploying** your server with proper security
4. **Testing** thoroughly before production use
5. **Monitoring** performance and security continuously

By following this guide, you can create robust MCP servers that safely and effectively extend ChatGPT's capabilities with your custom data sources and tools.

Remember:
- Start simple and iterate
- Prioritize security and privacy
- Test thoroughly
- Monitor continuously
- Follow best practices
- Join the community for support

Happy building! 🚀
