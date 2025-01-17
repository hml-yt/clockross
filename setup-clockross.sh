#!/bin/bash

# Install dependencies
apt-get update
apt-get upgrade -y
apt-get install -y python3 python3-pip python3-venv at

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

# Set up the services
cp setup/stable-diffusion.service setup/clockross.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable stable-diffusion
systemctl enable clockross
systemctl start stable-diffusion

# Set up the clockross environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
chown -R clockross:clockross /opt/clockross

# Configure sudoers for clockross user
echo "clockross ALL=(ALL) NOPASSWD: /usr/bin/shutdown" > /etc/sudoers.d/clockross
chmod 440 /etc/sudoers.d/clockross

# Set the default target to multi-user.target
systemctl set-default multi-user.target

# Write a finish-setup.sh script that runs 1 second after this script finishes, does init 3 and starts the clockross service
cat > /tmp/finish-setup.sh << 'EOF'
#!/bin/bash
systemctl isolate multi-user.target
sleep 5
systemctl start clockross
EOF
chmod +x /tmp/finish-setup.sh

# Run it in 1 with at
at now + 1 second < /tmp/finish-setup.sh