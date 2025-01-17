#!/bin/bash
# If there are no arguments, set the -d flag to run in detached mode
if [ -z "$1" ]; then
    docker run -d --restart=unless-stopped --runtime=nvidia --gpus all --network=host \
        -v /data/sd-webui-data:/data \
        --shm-size=8g \
        --name=stable-diffusion-webui \
        hackml/stable-diffusion-webui-jp61:r36.4.2

    # Show docker logs until we see the "Running on local URL" message
    docker logs -f stable-diffusion-webui | while read line; do
        echo "$line"
        if [[ "$line" == *"Running on local URL"* ]]; then
            pkill -P $$ docker
            break
        fi
    done
else
    docker run -it --runtime=nvidia --gpus all --network=host \
        -v /data/sd-webui-data:/data \
        hackml/stable-diffusion-webui-jp61 "$@"
fi