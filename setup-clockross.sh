#!/bin/bash

# Install dependencies
apt-get update
apt-get upgrade -y
apt-get install -y python3 python3-pip python3-venv at

# Install and enable persistent MAXN mode service
cp setup/jetson-maxn.service /etc/systemd/system/
systemctl enable jetson-maxn
systemctl start jetson-maxn

# Disable screensaver and screen blanking
sudo -u clockross dbus-launch gsettings set org.gnome.desktop.session idle-delay 0
sudo -u clockross dbus-launch gsettings set org.gnome.desktop.screensaver lock-enabled false
xset s off
xset -dpms
xset s noblank

# Set up the monitor configuration
cp setup/10-monitor.conf /etc/X11/xorg.conf.d/10-monitor.conf

# Create the clockross user
id -u clockross &>/dev/null || useradd -m clockross; usermod -aG sudo,docker clockross

# Clone the clockross repository
git clone https://github.com/hml-yt/clockross-cursor.git /opt/clockross
cd /opt/clockross

# Create /data directory and set ownership
mkdir -p /data/sd-webui-data
chown clockross:clockross -R /data

# Run the stable diffusion container
su clockross -c "/opt/clockross/setup/docker-run.sh"

# Set the default target to multi-user.target
systemctl set-default multi-user.target

# Set up the docker service
systemctl enable docker
systemctl start docker

# Set up the clockross service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
chown -R clockross:clockross /opt/clockross

# Configure sudoers for clockross user
echo "clockross ALL=(ALL) NOPASSWD: /usr/bin/shutdown" > /etc/sudoers.d/clockross
chmod 440 /etc/sudoers.d/clockross

# Set up the clockross service
cp setup/clockross.service /etc/systemd/system/clockross.service
systemctl enable clockross

# Reboot the system
reboot