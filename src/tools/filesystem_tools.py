"""Filesystem-related MCP tools."""

from typing import Dict, Any
from mcp.server.fastmcp import FastMCP

from services import FilesystemService


def register_filesystem_tools(mcp: FastMCP, filesystem_service: FilesystemService) -> None:
    """Register filesystem tools with the MCP server."""
    
    @mcp.tool()
    def filesystem_read_file(file_path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """
        Read the contents of a file.
        
        Use this to:
        - Read text files (code, config, logs, etc.)
        - Read binary files (use encoding='binary')
        - View file contents and metadata
        
        Security: Access is restricted to allowed directories (workspace, home, current directory).
        
        Args:
            file_path: Path to the file to read (can use ~ for home directory)
            encoding: Text encoding (default: 'utf-8'). Use 'binary' for binary files.
            
        Returns:
            dict: Contains file content, size, mime type, and metadata
            
        Example:
            >>> filesystem_read_file("~/myfile.txt")
            {
                "path": "/home/user/myfile.txt",
                "content": "Hello, world!",
                "size": 13,
                "mime_type": "text/plain",
                "encoding": "utf-8"
            }
        """
        return filesystem_service.read_file(file_path, encoding)
    
    @mcp.tool()
    def filesystem_write_file(
        file_path: str,
        content: str,
        encoding: str = "utf-8",
        create_dirs: bool = True
    ) -> Dict[str, Any]:
        """
        Write content to a file.
        
        Use this to:
        - Create new files
        - Update existing files
        - Save generated content
        
        Security: Access is restricted to allowed directories (workspace, home, current directory).
        
        Args:
            file_path: Path to the file to write (can use ~ for home directory)
            content: Content to write to the file
            encoding: Text encoding (default: 'utf-8')
            create_dirs: Create parent directories if they don't exist (default: True)
            
        Returns:
            dict: Contains operation result and file metadata
            
        Example:
            >>> filesystem_write_file("~/myfile.txt", "Hello, world!")
            {
                "success": True,
                "path": "/home/user/myfile.txt",
                "size": 13,
                "message": "File written successfully"
            }
        """
        return filesystem_service.write_file(file_path, content, encoding, create_dirs)
    
    @mcp.tool()
    def filesystem_list_directory(
        dir_path: str = ".",
        show_hidden: bool = False,
        recursive: bool = False
    ) -> Dict[str, Any]:
        """
        List contents of a directory.
        
        Use this to:
        - Browse filesystem structure
        - Find files and directories
        - Explore directory contents
        
        Security: Access is restricted to allowed directories (workspace, home, current directory).
        
        Args:
            dir_path: Path to directory (default: current directory, can use ~ for home)
            show_hidden: Include hidden files/directories (default: False)
            recursive: List subdirectories recursively (default: False)
            
        Returns:
            dict: Contains list of files and directories with metadata
            
        Example:
            >>> filesystem_list_directory("~/Documents")
            {
                "directory": "/home/user/Documents",
                "count": 5,
                "entries": [
                    {
                        "name": "file.txt",
                        "path": "file.txt",
                        "absolute_path": "/home/user/Documents/file.txt",
                        "type": "file",
                        "size": 1024,
                        "modified": 1234567890.0
                    },
                    ...
                ]
            }
        """
        return filesystem_service.list_directory(dir_path, show_hidden, recursive)
    
    @mcp.tool()
    def filesystem_create_directory(dir_path: str, parents: bool = True) -> Dict[str, Any]:
        """
        Create a directory.
        
        Use this to:
        - Create new directories
        - Set up project structure
        - Organize files
        
        Security: Access is restricted to allowed directories (workspace, home, current directory).
        
        Args:
            dir_path: Path to directory to create (can use ~ for home directory)
            parents: Create parent directories if they don't exist (default: True)
            
        Returns:
            dict: Contains operation result
            
        Example:
            >>> filesystem_create_directory("~/projects/myproject")
            {
                "success": True,
                "path": "/home/user/projects/myproject",
                "message": "Directory created successfully"
            }
        """
        return filesystem_service.create_directory(dir_path, parents)
    
    @mcp.tool()
    def filesystem_delete_path(path: str, recursive: bool = False) -> Dict[str, Any]:
        """
        Delete a file or directory.
        
        Use this to:
        - Remove files
        - Delete directories
        - Clean up temporary files
        
        Security: Access is restricted to allowed directories (workspace, home, current directory).
        
        Args:
            path: Path to delete (can use ~ for home directory)
            recursive: Allow deleting non-empty directories (default: False)
            
        Returns:
            dict: Contains operation result
            
        Example:
            >>> filesystem_delete_path("~/tempfile.txt")
            {
                "success": True,
                "path": "/home/user/tempfile.txt",
                "message": "File deleted successfully"
            }
        """
        return filesystem_service.delete_path(path, recursive)
    
    @mcp.tool()
    def filesystem_get_info(path: str) -> Dict[str, Any]:
        """
        Get information about a file or directory.
        
        Use this to:
        - Check if a path exists
        - Get file/directory metadata
        - Check file size and permissions
        
        Security: Access is restricted to allowed directories (workspace, home, current directory).
        
        Args:
            path: Path to inspect (can use ~ for home directory)
            
        Returns:
            dict: Contains path information including size, type, timestamps
            
        Example:
            >>> filesystem_get_info("~/myfile.txt")
            {
                "exists": True,
                "path": "/home/user/myfile.txt",
                "type": "file",
                "size": 1024,
                "modified": 1234567890.0,
                "mime_type": "text/plain",
                "permissions": "644"
            }
        """
        return filesystem_service.get_path_info(path)
