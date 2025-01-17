#!/bin/bash

# Install dependencies
sudo apt-get update

# Create the clockross user
sudo useradd -m clockross
sudo usermod -aG sudo clockross

# Run the stable diffusion container
docker run -d --restart=unless-stopped --runtime=nvidia --gpus all --network=host \
    -v /mnt/ssd/sd-webui-data:/data \
    --shm-size=8g \
    hackml/stable-diffusion-webui-jp61:r36.4.2


echo "Waiting stable diffusion to launch on 7860..."

while ! nc -z localhost 7860; do   
  sleep 0.1 # wait for 1/10 of the second before check again
done

echo "Stable diffusion launched"

# Set up the monitor configuration
cp setup/10-monitor.conf /etc/X11/xorg.conf.d/10-monitor.conf

# Set the default target to multi-user.target
sudo systemctl set-default multi-user.target

# Set up the docker service
sudo systemctl enable docker
sudo systemctl start docker

# Set up the clockross service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up the clockross service
cp setup/clockross.service /etc/systemd/system/clockross.service
sudo systemctl enable clockross
sudo systemctl start clockross
