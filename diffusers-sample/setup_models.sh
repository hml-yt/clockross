#!/bin/bash

# Create models directory if it doesn't exist
mkdir -p models

# Define model filenames and URLs as separate arrays
filenames=(
    "revAnimated_v2Rebirth.safetensors"
    "abstractPhoto_abcevereMix.safetensors"
    "control_v11f1e_sd15_tile.safetensors"
    "vae-ft-mse-840000-ema-pruned.safetensors"
)

urls=(
    "https://civitai.com/api/download/models/425083?type=Model&format=SafeTensor&size=full&fp=fp16&token=e73d59d536fa858d3dc918289851d39f"
    "https://civitai.com/api/download/models/115588?type=Model&format=SafeTensor&size=full&fp=fp16&token=e73d59d536fa858d3dc918289851d39f"
    "https://huggingface.co/nolanaatama/models/resolve/main/control_v11f1e_sd15_tile_fp16.safetensors"
    "https://huggingface.co/stabilityai/sd-vae-ft-mse-original/resolve/main/vae-ft-mse-840000-ema-pruned.safetensors"
)

# Function to download a model if it doesn't exist
download_model() {
    local filename=$1
    local url=$2
    local filepath="models/$filename"

    if [ ! -f "$filepath" ]; then
        echo "Downloading $filename..."
        wget -O "$filepath" "$url"
        if [ $? -eq 0 ]; then
            echo "✓ Successfully downloaded $filename"
        else
            echo "✗ Failed to download $filename"
            return 1
        fi
    else
        echo "→ $filename already exists, skipping download..."
    fi
}

# Process all models
echo "Processing models..."
for i in "${!filenames[@]}"; do
    download_model "${filenames[$i]}" "${urls[$i]}"
done

echo "All models processed successfully!" 