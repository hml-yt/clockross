#!/bin/bash

# Function to cleanup processes on exit
cleanup() {
    # Only cleanup if we're not running as a service
    if [ -z "$INVOCATION_ID" ]; then
        echo "Cleaning up..."
        docker stop stable-diffusion-webui >/dev/null 2>&1
        docker rm stable-diffusion-webui >/dev/null 2>&1
        pkill -P $$ docker
    fi
}

# Set up cleanup trap
trap cleanup EXIT

# Start the container
docker run --runtime=nvidia --gpus all --network=host \
    -v /data/sd-webui-data:/data \
    --shm-size=8g \
    --name=stable-diffusion-webui \
    hackml/stable-diffusion-webui-jp61 &
container_pid=$!

# Follow logs until the port is ready
docker logs -f stable-diffusion-webui &
while ! nc -z localhost 7860; do
    sleep 1
done

# Stop following logs and show ready message
pkill -P $$ docker
echo "Stable Diffusion WebUI is up and running!"

# If we're running as a service (systemd sets INVOCATION_ID), wait for the container
# Otherwise, exit and let the cleanup trap handle it
if [ -n "$INVOCATION_ID" ]; then
    # Notify systemd that we're ready
    systemd-notify --ready

    wait $container_pid
else
    exit 0
fi