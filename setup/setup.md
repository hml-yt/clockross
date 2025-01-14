2. Variant 2
    1. `sudo mkdir /opt/stable-diffusion-webui && chown $(USERNAME) /opt/stable-diffusion-webui`
    2. `sudo apt install python3.10-venv python-pip aria2`
    3. `sudo apt-get update && sudo apt-get install -y \
    google-perftools \
    libgoogle-perftools-dev \
    tesseract-ocr \
    libtesseract-dev \
    tesseract-ocr-eng`
    4. `git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui`
    5. `python -m vevn venv && source venv/bin/activate`
    6. `pip config set global.index-url https://pypi.jetson-ai-lab.dev/jp6/cu126/+simple/`
    7.  `printf "xfomers\ninsightface" >> requirements.txt && pip install -r requirements.txt` 
    8. Edit `webui-user.sh`, and add “--xformers --listen --api --enable-insecure-extension-access” to the COMMANDLINE_ARGS
    9. cd extensions
    10. `git clone https://github.com/BlafKing/sd-civitai-browser-plus`
    11. `git clone https://github.com/Mikubill/sd-webui-controlnet.git`
    12. cd sd-webui-controlnet/models
    13. `wget https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11f1e_sd15_tile_fp16.safetensors`
    14. back to root of stable-diffusion-webui
    15. `./webui.sh`