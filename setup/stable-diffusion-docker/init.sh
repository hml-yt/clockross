#!/bin/bash

# Function to copy template contents if destination is empty
copy_if_empty() {
    local src=$1
    local dst=$2
    
    # Check if destination is empty
    if [ -z "$(ls -A $dst 2>/dev/null)" ]; then
        echo "Initializing $dst with template content..."
        cp -r $src/* $dst/
    else
        echo "$dst already contains files, skipping initialization"
    fi
}

# Function to download ControlNet model if it doesn't exist
download_controlnet_model() {
    local model_path="/data/extensions/sd-webui-controlnet/models/control_v11f1e_sd15_tile_fp16.safetensors"
    if [ ! -f "$model_path" ]; then
        echo "Downloading ControlNet tile model..."
        mkdir -p "/data/extensions/sd-webui-controlnet/models"
        wget -nc -P "/data/extensions/sd-webui-controlnet/models" \
            https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11f1e_sd15_tile_fp16.safetensors
    else
        echo "ControlNet tile model already exists, skipping download"
    fi
}

# Copy template contents if mounted directories are empty
copy_if_empty /opt/stable-diffusion-webui/data-template /data

# Download ControlNet model if needed
download_controlnet_model

# Start the WebUI with all passed parameters
exec ./webui.sh "$@" 