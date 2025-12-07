"""Filesystem service for file and directory operations."""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import mimetypes

from config import get_settings


class FilesystemService:
    """Service for filesystem operations with security controls."""
    
    def __init__(self):
        self.settings = get_settings()
        # Define allowed base directories for operations
        # This prevents unauthorized access to system directories
        self.allowed_base_dirs = [
            self.settings.workspace_dir,
            Path.home(),  # User's home directory
            Path.cwd(),  # Current working directory
        ]
    
    def _is_path_allowed(self, path: Path) -> bool:
        """
        Check if a path is within allowed directories.
        
        This prevents access to sensitive system directories.
        
        Args:
            path: Path to check
            
        Returns:
            bool: True if path is allowed, False otherwise
        """
        try:
            resolved_path = path.resolve()
            # Check if path is within any allowed base directory
            for allowed_dir in self.allowed_base_dirs:
                try:
                    resolved_allowed = allowed_dir.resolve()
                    resolved_path.relative_to(resolved_allowed)
                    return True
                except ValueError:
                    continue
            return False
        except Exception:
            return False
    
    def read_file(self, file_path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """
        Read contents of a file.
        
        Args:
            file_path: Path to the file to read
            encoding: Text encoding (default: utf-8). Use 'binary' for binary files.
            
        Returns:
            dict: Contains file content and metadata
        """
        try:
            path = Path(file_path).expanduser()
            
            if not self._is_path_allowed(path):
                return {
                    "error": "Access denied",
                    "details": "Path is outside allowed directories"
                }
            
            if not path.exists():
                return {
                    "error": "File not found",
                    "details": f"File does not exist: {file_path}"
                }
            
            if not path.is_file():
                return {
                    "error": "Not a file",
                    "details": f"Path is not a file: {file_path}"
                }
            
            # Get file metadata
            stat = path.stat()
            mime_type, _ = mimetypes.guess_type(str(path))
            
            # Read file content
            if encoding == "binary":
                with open(path, "rb") as f:
                    content = f.read()
                return {
                    "path": str(path.resolve()),
                    "size": stat.st_size,
                    "mime_type": mime_type or "application/octet-stream",
                    "encoding": "binary",
                    "content_base64": content.hex(),  # Return as hex for JSON serialization
                    "is_binary": True
                }
            else:
                with open(path, "r", encoding=encoding) as f:
                    content = f.read()
                return {
                    "path": str(path.resolve()),
                    "size": stat.st_size,
                    "mime_type": mime_type or "text/plain",
                    "encoding": encoding,
                    "content": content,
                    "is_binary": False
                }
                
        except UnicodeDecodeError:
            return {
                "error": "Encoding error",
                "details": f"Cannot decode file with {encoding} encoding. Try 'binary' encoding."
            }
        except Exception as e:
            return {
                "error": "Failed to read file",
                "details": str(e)
            }
    
    def write_file(
        self,
        file_path: str,
        content: str,
        encoding: str = "utf-8",
        create_dirs: bool = True
    ) -> Dict[str, Any]:
        """
        Write content to a file.
        
        Args:
            file_path: Path to the file to write
            content: Content to write
            encoding: Text encoding (default: utf-8)
            create_dirs: Create parent directories if they don't exist
            
        Returns:
            dict: Contains operation result
        """
        try:
            path = Path(file_path).expanduser()
            
            if not self._is_path_allowed(path):
                return {
                    "error": "Access denied",
                    "details": "Path is outside allowed directories"
                }
            
            # Create parent directories if requested
            if create_dirs and not path.parent.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(path, "w", encoding=encoding) as f:
                f.write(content)
            
            return {
                "success": True,
                "path": str(path.resolve()),
                "size": len(content),
                "message": "File written successfully"
            }
                
        except Exception as e:
            return {
                "error": "Failed to write file",
                "details": str(e)
            }
    
    def list_directory(
        self,
        dir_path: str = ".",
        show_hidden: bool = False,
        recursive: bool = False
    ) -> Dict[str, Any]:
        """
        List contents of a directory.
        
        Args:
            dir_path: Path to directory (default: current directory)
            show_hidden: Include hidden files/directories
            recursive: List subdirectories recursively
            
        Returns:
            dict: Contains list of files and directories
        """
        try:
            path = Path(dir_path).expanduser()
            
            if not self._is_path_allowed(path):
                return {
                    "error": "Access denied",
                    "details": "Path is outside allowed directories"
                }
            
            if not path.exists():
                return {
                    "error": "Directory not found",
                    "details": f"Directory does not exist: {dir_path}"
                }
            
            if not path.is_dir():
                return {
                    "error": "Not a directory",
                    "details": f"Path is not a directory: {dir_path}"
                }
            
            entries = []
            
            if recursive:
                # Recursive listing
                for item in path.rglob("*"):
                    if not show_hidden and item.name.startswith("."):
                        continue
                    
                    try:
                        stat = item.stat()
                        entries.append({
                            "name": item.name,
                            "path": str(item.relative_to(path)),
                            "absolute_path": str(item.resolve()),
                            "type": "directory" if item.is_dir() else "file",
                            "size": stat.st_size if item.is_file() else 0,
                            "modified": stat.st_mtime
                        })
                    except Exception:
                        # Skip items we can't access
                        continue
            else:
                # Non-recursive listing
                for item in sorted(path.iterdir()):
                    if not show_hidden and item.name.startswith("."):
                        continue
                    
                    try:
                        stat = item.stat()
                        entries.append({
                            "name": item.name,
                            "path": str(item.relative_to(path)),
                            "absolute_path": str(item.resolve()),
                            "type": "directory" if item.is_dir() else "file",
                            "size": stat.st_size if item.is_file() else 0,
                            "modified": stat.st_mtime
                        })
                    except Exception:
                        # Skip items we can't access
                        continue
            
            return {
                "directory": str(path.resolve()),
                "count": len(entries),
                "entries": entries
            }
                
        except Exception as e:
            return {
                "error": "Failed to list directory",
                "details": str(e)
            }
    
    def create_directory(self, dir_path: str, parents: bool = True) -> Dict[str, Any]:
        """
        Create a directory.
        
        Args:
            dir_path: Path to directory to create
            parents: Create parent directories if they don't exist
            
        Returns:
            dict: Contains operation result
        """
        try:
            path = Path(dir_path).expanduser()
            
            if not self._is_path_allowed(path):
                return {
                    "error": "Access denied",
                    "details": "Path is outside allowed directories"
                }
            
            if path.exists():
                if path.is_dir():
                    return {
                        "success": True,
                        "path": str(path.resolve()),
                        "message": "Directory already exists"
                    }
                else:
                    return {
                        "error": "Path exists as file",
                        "details": f"A file already exists at: {dir_path}"
                    }
            
            path.mkdir(parents=parents, exist_ok=True)
            
            return {
                "success": True,
                "path": str(path.resolve()),
                "message": "Directory created successfully"
            }
                
        except Exception as e:
            return {
                "error": "Failed to create directory",
                "details": str(e)
            }
    
    def delete_path(self, path_str: str, recursive: bool = False) -> Dict[str, Any]:
        """
        Delete a file or directory.
        
        Args:
            path_str: Path to delete
            recursive: Allow deleting non-empty directories
            
        Returns:
            dict: Contains operation result
        """
        try:
            path = Path(path_str).expanduser()
            
            if not self._is_path_allowed(path):
                return {
                    "error": "Access denied",
                    "details": "Path is outside allowed directories"
                }
            
            if not path.exists():
                return {
                    "error": "Path not found",
                    "details": f"Path does not exist: {path_str}"
                }
            
            if path.is_file():
                path.unlink()
                return {
                    "success": True,
                    "path": str(path),
                    "message": "File deleted successfully"
                }
            elif path.is_dir():
                if recursive:
                    import shutil
                    shutil.rmtree(path)
                    return {
                        "success": True,
                        "path": str(path),
                        "message": "Directory deleted successfully"
                    }
                else:
                    path.rmdir()
                    return {
                        "success": True,
                        "path": str(path),
                        "message": "Directory deleted successfully"
                    }
            else:
                return {
                    "error": "Unknown path type",
                    "details": "Path is neither a file nor a directory"
                }
                
        except OSError as e:
            if "Directory not empty" in str(e):
                return {
                    "error": "Directory not empty",
                    "details": "Use recursive=True to delete non-empty directories"
                }
            return {
                "error": "Failed to delete path",
                "details": str(e)
            }
        except Exception as e:
            return {
                "error": "Failed to delete path",
                "details": str(e)
            }
    
    def get_path_info(self, path_str: str) -> Dict[str, Any]:
        """
        Get information about a path.
        
        Args:
            path_str: Path to inspect
            
        Returns:
            dict: Contains path information
        """
        try:
            path = Path(path_str).expanduser()
            
            if not self._is_path_allowed(path):
                return {
                    "error": "Access denied",
                    "details": "Path is outside allowed directories"
                }
            
            if not path.exists():
                return {
                    "exists": False,
                    "path": str(path)
                }
            
            stat = path.stat()
            mime_type, _ = mimetypes.guess_type(str(path))
            
            return {
                "exists": True,
                "path": str(path.resolve()),
                "type": "directory" if path.is_dir() else "file",
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "created": stat.st_ctime,
                "mime_type": mime_type,
                "is_symlink": path.is_symlink(),
                "permissions": oct(stat.st_mode)[-3:]
            }
                
        except Exception as e:
            return {
                "error": "Failed to get path info",
                "details": str(e)
            }
