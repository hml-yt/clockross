FROM nvcr.io/nvidia/l4t-base:r36.2.0

# Set environment variables for CUDA
ENV CUDA_HOME=/usr/local/cuda-12.2
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=/usr/local/cuda-12.2/lib64:/usr/lib/aarch64-linux-gnu

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10-venv \
    python-pip \
    aria2 \
    google-perftools \
    libgoogle-perftools-dev \
    tesseract-ocr \
    libtesseract-dev \
    tesseract-ocr-eng \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /opt/stable-diffusion-webui

# Clone the repository
RUN git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui .

# Create and activate virtual environment
RUN python3 -m venv venv
ENV PATH="/opt/stable-diffusion-webui/venv/bin:$PATH"

# Configure pip and install requirements
RUN pip config set global.index-url https://pypi.jetson-ai-lab.dev/jp6/cu126/+simple/ && \
    echo -e "xformers\ninsightface" >> requirements.txt && \
    pip install -r requirements.txt

# Configure webui settings for API mode
RUN sed -i 's/^export COMMANDLINE_ARGS=.*/export COMMANDLINE_ARGS="--xformers --listen --api --enable-insecure-extension-access"/' webui-user.sh

# Install extensions
WORKDIR /opt/stable-diffusion-webui/extensions
RUN git clone https://github.com/BlafKing/sd-civitai-browser-plus && \
    git clone https://github.com/Mikubill/sd-webui-controlnet.git

# Download ControlNet model
WORKDIR /opt/stable-diffusion-webui/extensions/sd-webui-controlnet/models
RUN wget https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11f1e_sd15_tile_fp16.safetensors

# Set working directory back to root
WORKDIR /opt/stable-diffusion-webui

# Create volume mount points for models and outputs
VOLUME ["/opt/stable-diffusion-webui/models", "/opt/stable-diffusion-webui/outputs"]

# Expose API port
EXPOSE 7860

# Start the WebUI in API mode
CMD ["./webui.sh", "--api"] 