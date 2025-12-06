# Web Control Panel and Auto-Start Setup

This document describes how to use the web control panel and set up auto-start for the CadSlicerPrinter MCP Server.

## Web Control Panel

### Overview

The CadSlicerPrinter server now includes a minimalist web-based control panel that provides an intuitive interface for managing all MCP server functions without requiring a separate MCP client.

### Features

- **CAD Operations**: Create, modify, and preview 3D models
- **Slicer Operations**: Slice models to generate G-code
- **Printer Operations**: Check printer status, upload files, and send G-code commands
- **Workspace Management**: List and manage all models in your workspace
- **Real-time Output**: View all operation results in a console-style output panel
- **Server Status**: Live connection status indicator

### Starting the Web Interface

You can start the server with the web interface in two ways:

#### Option 1: Using the --web flag
```bash
cd src
python server.py --web
```

#### Option 2: Using streamable-http transport
```bash
cd src
python server.py --transport streamable-http
```

#### Custom Port
By default, the web interface runs on port 8080. You can specify a different port:
```bash
python server.py --web --port 9000
```

### Accessing the Web Interface

Once the server is running, open your web browser and navigate to:
```
http://localhost:8080
```

Or if using a custom port:
```
http://localhost:9000
```

### Using the Web Interface

1. **Create a Model**: Enter a description in the "Create Model" section and click "Create Model"
2. **View Output**: Check the output panel at the bottom to see the model ID
3. **Render Preview**: Enter the model ID and click "Render Preview" to visualize it
4. **Modify Model**: Enter the model ID and modification instructions
5. **Slice Model**: Enter the model ID and slicer profile path to generate G-code
6. **Print**: Upload and start printing using the model ID

All operations display their results in the output panel, including any errors or success messages.

## Auto-Start Configuration

### Overview

The server can be configured to start automatically on system boot without requiring a GUI or system tray icon. This is ideal for:

- Running as a background service
- Headless servers
- Always-available 3D printing control
- Integration with home automation systems

### Installation (Linux with systemd)

1. **Navigate to the repository**:
   ```bash
   cd /path/to/Pc-MCP
   ```

2. **Run the installation script**:
   ```bash
   sudo ./install-autostart.sh
   ```

3. **Configure environment variables** (optional):
   Edit the service file if you need to customize paths:
   ```bash
   sudo nano /etc/systemd/system/cadslicerprinter@.service
   ```

   Update these environment variables as needed:
   - `WORKSPACE_DIR`: Where models are stored
   - `OPENSCAD_BIN`: Path to OpenSCAD executable
   - `SLICER_BIN`: Path to slicer executable
   - `OCTOPRINT_URL`: URL of your OctoPrint instance
   - `OCTOPRINT_API_KEY`: Your OctoPrint API key

4. **Start the service**:
   ```bash
   sudo systemctl start cadslicerprinter@$USER.service
   ```

5. **Verify it's running**:
   ```bash
   sudo systemctl status cadslicerprinter@$USER.service
   ```

   Access the web interface at http://localhost:8080

### Service Management

After installation, you can manage the service with these commands:

#### Start the service
```bash
sudo systemctl start cadslicerprinter@$USER.service
```

#### Stop the service
```bash
sudo systemctl stop cadslicerprinter@$USER.service
```

#### Restart the service
```bash
sudo systemctl restart cadslicerprinter@$USER.service
```

#### Check service status
```bash
sudo systemctl status cadslicerprinter@$USER.service
```

#### View logs
```bash
# Real-time logs
sudo journalctl -u cadslicerprinter@$USER.service -f

# Last 50 lines
sudo journalctl -u cadslicerprinter@$USER.service -n 50
```

#### Enable auto-start on boot
```bash
sudo systemctl enable cadslicerprinter@$USER.service
```

#### Disable auto-start on boot
```bash
sudo systemctl disable cadslicerprinter@$USER.service
```

### Manual Service File Installation

If you prefer to install the service file manually:

1. Copy the service file:
   ```bash
   sudo cp cadslicerprinter.service /etc/systemd/system/cadslicerprinter@.service
   ```

2. Edit the service file to update paths:
   ```bash
   sudo nano /etc/systemd/system/cadslicerprinter@.service
   ```
   
   Replace `/home/%i/Pc-MCP` with your actual repository path.

3. Reload systemd:
   ```bash
   sudo systemctl daemon-reload
   ```

4. Enable and start:
   ```bash
   sudo systemctl enable cadslicerprinter@$USER.service
   sudo systemctl start cadslicerprinter@$USER.service
   ```

### Windows Auto-Start

For Windows systems, you can use Task Scheduler:

1. Open Task Scheduler
2. Create a new task
3. Set trigger to "At startup"
4. Set action to run:
   ```
   python C:\path\to\Pc-MCP\src\server.py --web
   ```
5. Configure to run whether user is logged in or not
6. Set to run in the background (hidden)

### macOS Auto-Start

For macOS systems, create a LaunchAgent:

1. Create a plist file at `~/Library/LaunchAgents/com.cadslicerprinter.plist`:
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>Label</key>
       <string>com.cadslicerprinter</string>
       <key>ProgramArguments</key>
       <array>
           <string>/usr/bin/python3</string>
           <string>/path/to/Pc-MCP/src/server.py</string>
           <string>--web</string>
       </array>
       <key>RunAtLoad</key>
       <true/>
       <key>KeepAlive</key>
       <true/>
   </dict>
   </plist>
   ```

2. Load the agent:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.cadslicerprinter.plist
   ```

## Troubleshooting

### Service won't start
1. Check the service logs:
   ```bash
   sudo journalctl -u cadslicerprinter@$USER.service -n 50
   ```

2. Verify Python dependencies are installed:
   ```bash
   pip install -e .
   ```

3. Check file permissions

### Web interface not accessible
1. Verify the service is running:
   ```bash
   sudo systemctl status cadslicerprinter@$USER.service
   ```

2. Check if port 8080 is available:
   ```bash
   netstat -tlnp | grep 8080
   ```

3. Try a different port:
   ```bash
   python server.py --web --port 9000
   ```

### Can't connect to OctoPrint
1. Verify OctoPrint is running
2. Check the OCTOPRINT_URL and OCTOPRINT_API_KEY in the service file
3. Restart the service after making changes

## Security Considerations

- The web interface listens on all network interfaces (0.0.0.0) by default
- Consider using a reverse proxy (nginx, Apache) with authentication for production use
- Set firewall rules to restrict access to port 8080 if needed
- Store OctoPrint API keys securely
- Run the service as a non-privileged user (default behavior)

## Integration with MCP Clients

The server maintains full backward compatibility with MCP clients:

- **stdio transport**: Use for OpenAI and other MCP-compatible clients
- **sse transport**: Use for server-sent events based clients  
- **streamable-http**: Automatically enables web interface
- **Web API**: REST-like endpoints at `/api/*` for custom integrations

All transports can be used simultaneously by running multiple instances on different ports.
