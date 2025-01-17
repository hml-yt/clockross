#!/bin/bash

# Start the container
docker run --runtime=nvidia --gpus all --network=host \
    -v /data/sd-webui-data:/data \
    --shm-size=8g \
    --name=stable-diffusion-webui \
    hackml/stable-diffusion-webui-jp61:r36.4.2 &

# Follow logs until the port is ready
docker logs -f stable-diffusion-webui &
while ! nc -z localhost 7860; do
    sleep 1
done

# Stop following logs and show ready message
pkill -P $$ docker
echo "Stable Diffusion WebUI is up and running!"

# Notify systemd that we're ready
systemd-notify --ready

# Keep the container running
wait $(jobs -p | head -n1)