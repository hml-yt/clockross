#!/bin/bash
docker build -t hackml/stable-diffusion-webui-jp61 $(dirname "$0")/stable-diffusion-docker && \
docker tag hackml/stable-diffusion-webui-jp61 hackml/stable-diffusion-webui-jp61:latest && \
docker push hackml/stable-diffusion-webui-jp61:latest
