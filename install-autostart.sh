#!/bin/bash
# Installation script for CadSlicerPrinter MCP Server auto-start with Cloudflared Tunnel

set -e

echo "=========================================="
echo "CadSlicerPrinter Auto-Start Installation"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "This script must be run as root (use sudo)"
    exit 1
fi

# Get the actual user (not root)
ACTUAL_USER="${SUDO_USER:-$USER}"
if [ "$ACTUAL_USER" = "root" ]; then
    echo "Error: Could not determine the actual user"
    echo "Please run this script with sudo as a regular user"
    exit 1
fi

echo "Installing service for user: $ACTUAL_USER"

# Get the repository path
REPO_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Repository path: $REPO_PATH"

# Install main service
SERVICE_FILE="$REPO_PATH/cadslicerprinter.service"
SYSTEMD_DIR="/etc/systemd/system"

if [ ! -f "$SERVICE_FILE" ]; then
    echo "Error: Service file not found at $SERVICE_FILE"
    exit 1
fi

# Create a modified service file with actual paths
# We keep User=%i so systemd can substitute the username from the instance name
TEMP_SERVICE="/tmp/cadslicerprinter@.service"

# Replace path placeholders but keep User=%i intact
sed -e "s|WorkingDirectory=/home/%i/Pc-MCP/src|WorkingDirectory=$REPO_PATH/src|g" \
    -e "s|Environment=\"WORKSPACE_DIR=/home/%i/Pc-MCP/workspace\"|Environment=\"WORKSPACE_DIR=$REPO_PATH/workspace\"|g" \
    -e "s|/home/%i/Pc-MCP/src/server.py|$REPO_PATH/src/server.py|g" \
    "$SERVICE_FILE" > "$TEMP_SERVICE"

echo "Installing CadSlicerPrinter systemd service..."
cp "$TEMP_SERVICE" "$SYSTEMD_DIR/cadslicerprinter@.service"
rm "$TEMP_SERVICE"

# Install cloudflared tunnel service (optional)
CLOUDFLARED_SERVICE_FILE="$REPO_PATH/cloudflared-pcmcp.service"
if [ -f "$CLOUDFLARED_SERVICE_FILE" ]; then
    TEMP_CLOUDFLARED_SERVICE="/tmp/cloudflared-pcmcp@.service"
    
    # Replace path placeholders but keep User=%i intact
    sed -e "s|WorkingDirectory=/home/%i/Pc-MCP|WorkingDirectory=$REPO_PATH|g" \
        "$CLOUDFLARED_SERVICE_FILE" > "$TEMP_CLOUDFLARED_SERVICE"
    
    echo "Installing Cloudflared tunnel systemd service..."
    cp "$TEMP_CLOUDFLARED_SERVICE" "$SYSTEMD_DIR/cloudflared-pcmcp@.service"
    rm "$TEMP_CLOUDFLARED_SERVICE"
    
    CLOUDFLARED_INSTALLED=true
else
    echo "Cloudflared service file not found, skipping..."
    CLOUDFLARED_INSTALLED=false
fi

# Reload systemd
echo "Reloading systemd daemon..."
systemctl daemon-reload

# Enable and start the service
echo "Enabling CadSlicerPrinter service for user $ACTUAL_USER..."
systemctl enable "cadslicerprinter@$ACTUAL_USER.service"

# Enable cloudflared if installed
if [ "$CLOUDFLARED_INSTALLED" = true ]; then
    echo "Enabling Cloudflared tunnel service for user $ACTUAL_USER..."
    systemctl enable "cloudflared-pcmcp@$ACTUAL_USER.service"
fi

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "The CadSlicerPrinter server will now start automatically on boot."
echo ""
echo "Useful commands:"
echo "  Start service:   sudo systemctl start cadslicerprinter@$ACTUAL_USER.service"
echo "  Stop service:    sudo systemctl stop cadslicerprinter@$ACTUAL_USER.service"
echo "  Check status:    sudo systemctl status cadslicerprinter@$ACTUAL_USER.service"
echo "  View logs:       sudo journalctl -u cadslicerprinter@$ACTUAL_USER.service -f"
echo "  Disable autorun: sudo systemctl disable cadslicerprinter@$ACTUAL_USER.service"
echo ""
echo "To start the service now, run:"
echo "  sudo systemctl start cadslicerprinter@$ACTUAL_USER.service"
echo ""
echo "Web interface will be available at: http://localhost:8080"
echo ""
