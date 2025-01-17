FROM nvcr.io/nvidia/l4t-jetpack:r36.4.0

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    python3-venv \
    python3-pip \
    aria2 \
    google-perftools \
    tesseract-ocr \
    libtesseract-dev \
    tesseract-ocr-eng \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Add user
RUN useradd -m sduser -u 1000
USER sduser

# Clone the repository
WORKDIR /opt/stable-diffusion-webui
RUN git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui .

# Setup Python environment and install dependencies in one layer
RUN python3 -m venv venv
ENV PATH="/opt/stable-diffusion-webui/venv/bin:$PATH"

# Install dependencies with xformers and insightface
RUN pip config set global.index-url https://pypi.jetson-ai-lab.dev/jp6/cu126/+simple/ && \
    pip install wheel && \
    pip install -r requirements.txt && \
    pip install --no-deps insightface onnxruntime-gpu opencv-python-headless xformers

# Edit webui-user.sh
RUN sed -i 's/^#export COMMANDLINE_ARGS=""/export COMMANDLINE_ARGS="--xformers --enable-insecure-extension-access --listen --api --data-dir=\/data"/' webui-user.sh

# Install extensions
WORKDIR /data/extensions
RUN git clone https://github.com/Mikubill/sd-webui-controlnet && \
    git clone https://github.com/zanllp/sd-webui-infinite-image-browsing && \
    git clone https://github.com/thomasasfk/sd-webui-aspect-ratio-helper && \
    git clone https://github.com/BlafKing/sd-civitai-browser-plus

# Prepare environment and run tests in one layer
WORKDIR /opt/stable-diffusion-webui
RUN COMMANDLINE_ARGS="--skip-python-version-check --skip-torch-cuda-test --data-dir=/data" \
    python -c 'from modules import launch_utils; launch_utils.prepare_environment()' && \
    python launch.py --help && \ 
    pip show insightface

# Move extensions and models to data directory
RUN mkdir -p template && \
    mv /data/extensions template/extensions

# Copy init.sh
ADD --chmod=755 init.sh ./

# Set environment variables
ENV TRANSFORMERS_CACHE=/data/transformers
ENV HF_HOME=/data/hf
ENV HF_HUB_CACHE=/data/hf

# Run the application
CMD ["./init.sh"]
