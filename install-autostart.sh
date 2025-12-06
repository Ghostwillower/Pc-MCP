#!/bin/bash
# Installation script for CadSlicerPrinter MCP Server auto-start

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

# Copy service file to systemd directory
SERVICE_FILE="$REPO_PATH/cadslicerprinter.service"
SYSTEMD_DIR="/etc/systemd/system"

if [ ! -f "$SERVICE_FILE" ]; then
    echo "Error: Service file not found at $SERVICE_FILE"
    exit 1
fi

# Update the service file with the actual paths
TEMP_SERVICE="/tmp/cadslicerprinter@.service"
sed "s|/home/%i/Pc-MCP|$REPO_PATH|g" "$SERVICE_FILE" > "$TEMP_SERVICE"

echo "Installing systemd service..."
cp "$TEMP_SERVICE" "$SYSTEMD_DIR/cadslicerprinter@.service"
rm "$TEMP_SERVICE"

# Reload systemd
echo "Reloading systemd daemon..."
systemctl daemon-reload

# Enable and start the service
echo "Enabling service for user $ACTUAL_USER..."
systemctl enable "cadslicerprinter@$ACTUAL_USER.service"

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
