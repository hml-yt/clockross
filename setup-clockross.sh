#!/bin/bash

# Install dependencies
sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv

# Create the clockross user
sudo useradd -m clockross

# Clone the clockross repository
git clone https://github.com/hackml/clockross.git /opt/clockross
cd /opt/clockross

# Set up the monitor configuration
cp setup/10-monitor.conf /etc/X11/xorg.conf.d/10-monitor.conf

# Run the stable diffusion container
source /opt/clockross/setup/docker-run.sh

# Set the default target to multi-user.target
sudo systemctl set-default multi-user.target

# Set up the docker service
sudo systemctl enable docker
sudo systemctl start docker

# Set up the clockross service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
chown -R clockross:clockross /opt/clockross

# Configure sudoers for clockross user
echo "clockross ALL=(ALL) NOPASSWD: /usr/bin/shutdown" | sudo tee /etc/sudoers.d/clockross
sudo chmod 440 /etc/sudoers.d/clockross

# Set up the clockross service
cp setup/clockross.service /etc/systemd/system/clockross.service
sudo systemctl enable clockross
sudo systemctl start clockross
