# Filesystem and Terminal Tools

This document describes the filesystem and terminal tools available in the CAD-Slicer-Printer MCP server.

## Overview

The MCP server now includes tools for:
- **Filesystem Operations**: View and modify files and directories
- **Terminal Commands**: Execute shell commands safely without admin privileges

All operations include security controls to prevent unauthorized access and privilege escalation.

## Security Model

### Filesystem Access
- **Allowed Directories**: Operations are restricted to:
  - Workspace directory (`WORKSPACE_DIR` environment variable)
  - User's home directory (`~`)
  - Current working directory
- **Blocked Access**: Attempts to access system directories (e.g., `/etc`, `/sys`, `/root`) are denied
- **Path Resolution**: All paths are resolved and validated before operations

### Terminal Commands
- **Blocked Commands**: Commands requiring admin/root privileges are blocked:
  - Privilege escalation: `sudo`, `su`, `doas`, `pkexec`
  - Permission changes: `chmod`, `chown`, `chgrp`
  - System management: `systemctl`, `service`, `reboot`, `shutdown`
  - Disk operations: `mkfs`, `fdisk`, `mount`, `umount`
  - Firewall: `iptables`, `ufw`, `firewall-cmd`
  - User management: `useradd`, `usermod`, `passwd`
- **Working Directory**: Command execution is restricted to allowed directories
- **Environment**: Sensitive environment variables (containing KEY, SECRET, PASSWORD, TOKEN, CREDENTIAL) are redacted

## Filesystem Tools

### filesystem_read_file

Read the contents of a file.

**Arguments:**
- `file_path` (string): Path to the file to read (can use `~` for home directory)
- `encoding` (string, optional): Text encoding (default: `utf-8`). Use `'binary'` for binary files.

**Returns:**
- `path`: Absolute path to the file
- `content`: File contents (or `content_base64` for binary files)
- `size`: File size in bytes
- `mime_type`: Detected MIME type
- `encoding`: Encoding used
- `is_binary`: Whether the file is binary

**Example:**
```json
{
  "file_path": "~/myproject/config.json",
  "encoding": "utf-8"
}
```

### filesystem_write_file

Write content to a file.

**Arguments:**
- `file_path` (string): Path to the file to write
- `content` (string): Content to write to the file
- `encoding` (string, optional): Text encoding (default: `utf-8`)
- `create_dirs` (boolean, optional): Create parent directories if they don't exist (default: `true`)

**Returns:**
- `success`: Operation success status
- `path`: Absolute path to the file
- `size`: Number of bytes written
- `message`: Success message

**Example:**
```json
{
  "file_path": "~/myproject/output.txt",
  "content": "Hello, World!",
  "create_dirs": true
}
```

### filesystem_list_directory

List contents of a directory.

**Arguments:**
- `dir_path` (string, optional): Path to directory (default: current directory)
- `show_hidden` (boolean, optional): Include hidden files/directories (default: `false`)
- `recursive` (boolean, optional): List subdirectories recursively (default: `false`)

**Returns:**
- `directory`: Absolute path to the directory
- `count`: Number of entries
- `entries`: Array of file/directory information
  - `name`: Entry name
  - `path`: Relative path
  - `absolute_path`: Absolute path
  - `type`: `"file"` or `"directory"`
  - `size`: Size in bytes (0 for directories)
  - `modified`: Modification timestamp

**Example:**
```json
{
  "dir_path": "~/myproject",
  "show_hidden": false,
  "recursive": false
}
```

### filesystem_create_directory

Create a directory.

**Arguments:**
- `dir_path` (string): Path to directory to create
- `parents` (boolean, optional): Create parent directories if they don't exist (default: `true`)

**Returns:**
- `success`: Operation success status
- `path`: Absolute path to the directory
- `message`: Success message

**Example:**
```json
{
  "dir_path": "~/myproject/data/temp",
  "parents": true
}
```

### filesystem_delete_path

Delete a file or directory.

**Arguments:**
- `path` (string): Path to delete
- `recursive` (boolean, optional): Allow deleting non-empty directories (default: `false`)

**Returns:**
- `success`: Operation success status
- `path`: Path that was deleted
- `message`: Success message

**Example:**
```json
{
  "path": "~/myproject/temp",
  "recursive": true
}
```

### filesystem_get_info

Get information about a file or directory.

**Arguments:**
- `path` (string): Path to inspect

**Returns:**
- `exists`: Whether the path exists
- `path`: Absolute path
- `type`: `"file"` or `"directory"`
- `size`: Size in bytes
- `modified`: Modification timestamp
- `created`: Creation timestamp
- `mime_type`: Detected MIME type
- `is_symlink`: Whether the path is a symbolic link
- `permissions`: File permissions (octal)

**Example:**
```json
{
  "path": "~/myproject/README.md"
}
```

## Terminal Tools

### terminal_execute

Execute a terminal command safely without admin privileges.

**Arguments:**
- `command` (string): Command to execute (shell syntax supported)
- `working_dir` (string, optional): Working directory for command execution (default: workspace)
- `timeout` (integer, optional): Timeout in seconds (uses config default if not specified)

**Returns:**
- `success`: Whether the command executed successfully
- `command`: The command that was executed
- `working_dir`: Working directory used
- `exit_code`: Command exit code
- `stdout`: Standard output
- `stderr`: Standard error

**Example:**
```json
{
  "command": "python script.py --verbose",
  "working_dir": "~/myproject",
  "timeout": 60
}
```

**Blocked Commands Example:**
```json
{
  "command": "sudo apt update"
}
```
Response:
```json
{
  "error": "Command blocked",
  "details": "Command 'sudo' requires admin privileges and is blocked"
}
```

### terminal_get_cwd

Get the current working directory.

**Arguments:** None

**Returns:**
- `current_directory`: Current working directory path
- `is_allowed`: Whether the directory is in an allowed location

**Example:**
```json
{}
```

### terminal_get_env

Get environment variables.

**Arguments:** None

**Returns:**
- `environment_variables`: Object containing environment variables (sensitive ones redacted)
- `count`: Number of environment variables

**Example:**
```json
{}
```

## Use Cases

### Development Workflow

1. **Browse project structure:**
   ```json
   {"dir_path": "~/myproject", "recursive": true}
   ```

2. **Read configuration file:**
   ```json
   {"file_path": "~/myproject/config.json"}
   ```

3. **Run tests:**
   ```json
   {"command": "npm test", "working_dir": "~/myproject"}
   ```

4. **Save results:**
   ```json
   {
     "file_path": "~/myproject/results.txt",
     "content": "Test results..."
   }
   ```

### File Management

1. **Create project directory:**
   ```json
   {"dir_path": "~/newproject/src"}
   ```

2. **Write source file:**
   ```json
   {
     "file_path": "~/newproject/src/main.py",
     "content": "print('Hello, World!')"
   }
   ```

3. **Check file info:**
   ```json
   {"path": "~/newproject/src/main.py"}
   ```

### Code Building

1. **Check working directory:**
   ```json
   {}
   ```

2. **Build project:**
   ```json
   {
     "command": "npm run build",
     "working_dir": "~/myproject",
     "timeout": 300
   }
   ```

3. **List build artifacts:**
   ```json
   {"dir_path": "~/myproject/dist"}
   ```

## Best Practices

### Filesystem Operations
- Use `~` for home directory paths to ensure portability
- Check if files exist before reading with `filesystem_get_info`
- Use `create_dirs=true` when writing files to new locations
- Be careful with `recursive=true` when deleting directories

### Terminal Commands
- Specify working directory to avoid ambiguity
- Set appropriate timeouts for long-running commands
- Check exit codes to verify command success
- Read both stdout and stderr for complete output

### Security
- Never try to access system directories outside allowed paths
- Don't attempt to escalate privileges
- Be aware that sensitive environment variables are redacted
- Use file permissions appropriately

## Error Handling

All tools return error information when operations fail:

```json
{
  "error": "Error type",
  "details": "Detailed error message"
}
```

Common errors:
- `"Access denied"`: Path is outside allowed directories
- `"File not found"`: File or directory doesn't exist
- `"Command blocked"`: Command requires admin privileges
- `"Encoding error"`: Cannot decode file with specified encoding

## Environment Variables

The following environment variables affect filesystem and terminal operations:

- `WORKSPACE_DIR`: Base directory for operations (default: `./workspace`)
- `COMMAND_TIMEOUT`: Default timeout for commands in seconds (default: 120)
- `MAX_OUTPUT_LENGTH`: Maximum output length for commands (default: 10000)

## Version History

- **v0.2.1** (2025-12-07): Added filesystem and terminal tools with security controls
- **v0.2.0**: Initial redesigned version with 3D printing tools
