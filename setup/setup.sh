#!/bin/bash

# Exit on error
set -e

# Set default installation prefix if not specified
INSTALL_PREFIX="${INSTALL_PREFIX:-/opt}"

echo "Starting Stable Diffusion WebUI setup..."
echo "Installation prefix: $INSTALL_PREFIX"

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Please run this script as a regular user, not root"
    exit 1
fi

# Create installation directory
echo "Creating installation directory..."
sudo mkdir -p "$INSTALL_PREFIX"
sudo chown $USER "$INSTALL_PREFIX"
cd "$INSTALL_PREFIX"

# Create and enter stable-diffusion-webui directory
mkdir -p stable-diffusion-webui
cd stable-diffusion-webui

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    python3.10-venv \
    python-pip \
    aria2 \
    google-perftools \
    libgoogle-perftools-dev \
    tesseract-ocr \
    libtesseract-dev \
    tesseract-ocr-eng

# Clone the repository contents to current directory
echo "Cloning Stable Diffusion WebUI repository..."
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui .

# Setup Python virtual environment
echo "Setting up Python virtual environment..."
python -m venv venv
source venv/bin/activate

# Configure pip and install requirements
echo "Configuring pip and installing requirements..."
pip config set global.index-url https://pypi.jetson-ai-lab.dev/jp6/cu126/+simple/
echo -e "xformers\ninsightface" >> requirements.txt
pip install -r requirements.txt

# Configure webui-user.sh
echo "Configuring WebUI settings..."
sed -i 's/^export COMMANDLINE_ARGS=.*/export COMMANDLINE_ARGS="--xformers --listen --api --enable-insecure-extension-access"/' webui-user.sh

# Install extensions
echo "Installing extensions..."
cd extensions
git clone https://github.com/BlafKing/sd-civitai-browser-plus
git clone https://github.com/Mikubill/sd-webui-controlnet.git

# Download ControlNet model
echo "Downloading ControlNet model..."
cd sd-webui-controlnet/models
wget https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11f1e_sd15_tile_fp16.safetensors

# Return to root directory and start WebUI
cd ../../..
echo "Setup complete! Starting Stable Diffusion WebUI..."
./webui.sh 