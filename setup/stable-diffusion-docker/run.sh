#!/bin/bash
docker run -it --rm -d --restart=unless-stopped --runtime=nvidia --gpus all --network=host -v /mnt/ssd/sd-webui-data:/data stable-diffusion-webui-jp61 "$@"