#!/bin/bash

# Exit on error
set -e

# Check for required tools
if ! command -v jq >/dev/null 2>&1; then
    echo "Error: jq is required but not installed."
    echo "Install it with: sudo apt-get install jq"
    exit 1
fi

# Set default storage location if not specified
DOCKER_ROOT="${DOCKER_ROOT:-/data/docker}"

echo "Configuring Docker storage location..."
echo "Target location: $DOCKER_ROOT"

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Please run this script as a regular user, not root"
    exit 1
fi

# Stop Docker service
echo "Stopping Docker service..."
sudo systemctl stop docker.service
sudo systemctl stop docker.socket

# Create new Docker root directory
echo "Creating new Docker root directory..."
sudo mkdir -p "$DOCKER_ROOT"

# Move existing Docker data if it exists
if [ -d "/var/lib/docker" ]; then
    echo "Moving existing Docker data..."
    sudo rsync -aP /var/lib/docker/ "$DOCKER_ROOT/"
    sudo mv /var/lib/docker /var/lib/docker.old
fi

# Update Docker daemon configuration
echo "Configuring Docker daemon..."
sudo mkdir -p /etc/docker
DAEMON_FILE="/etc/docker/daemon.json"

# Read existing config or create new one
if [ -f "$DAEMON_FILE" ]; then
    echo "Updating existing daemon.json..."
    TMP_CONFIG=$(mktemp)
    jq --arg root "$DOCKER_ROOT" '. + {"data-root": $root}' "$DAEMON_FILE" > "$TMP_CONFIG"
    sudo mv "$TMP_CONFIG" "$DAEMON_FILE"
else
    echo "Creating new daemon.json..."
    sudo tee "$DAEMON_FILE" > /dev/null <<EOF
{
    "data-root": "$DOCKER_ROOT"
}
EOF
fi

# Start Docker service
echo "Starting Docker service..."
sudo systemctl start docker

# Verify the new configuration
echo "Verifying configuration..."
docker info | grep "Docker Root Dir"

# Clean up old data if everything is working
echo "If everything is working correctly, you can remove the old data with:"
echo "sudo rm -rf /var/lib/docker.old" 