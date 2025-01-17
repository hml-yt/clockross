#!/bin/bash

# Color definitions
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting ClockRoss Setup...${NC}\n"

# Install dependencies
echo -e "${YELLOW}Step 1: Installing system dependencies...${NC}"
apt-get update && apt-get install -y python3 python3-pip python3-venv
echo -e "${GREEN}✓ Dependencies installed successfully${NC}\n"

# Disable screensaver and screen blanking
echo -e "${YELLOW}Step 2: Configuring display settings...${NC}"
sudo -u clockross dbus-launch gsettings set org.gnome.desktop.session idle-delay 0
sudo -u clockross dbus-launch gsettings set org.gnome.desktop.screensaver lock-enabled false
sudo -u clockross dbus-launch gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'
xset s off
xset -dpms
xset s noblank
echo -e "${GREEN}✓ Display settings configured${NC}\n"

# Create the clockross user
echo -e "${YELLOW}Step 3: Setting up clockross user...${NC}"
id -u clockross &>/dev/null || useradd -m clockross; usermod -aG sudo,docker clockross
echo -e "${GREEN}✓ User setup complete${NC}\n"

# Clone the clockross repository
echo -e "${YELLOW}Step 4: Cloning ClockRoss repository...${NC}"
git clone https://github.com/hml-yt/clockross-cursor.git /opt/clockross
cd /opt/clockross
echo -e "${GREEN}✓ Repository cloned successfully${NC}\n"

# Create /data directory and set ownership
echo -e "${YELLOW}Step 5: Setting up data directory...${NC}"
mkdir -p /data/sd-webui-data
chown clockross:clockross -R /data
echo -e "${GREEN}✓ Data directory created and configured${NC}\n"

# Set up the services
echo -e "${YELLOW}Step 6: Configuring system services...${NC}"
cp setup/stable-diffusion.service setup/clockross.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable stable-diffusion
systemctl enable clockross
echo -e "${GREEN}✓ Services configured${NC}\n"

echo -e "${YELLOW}Starting Stable Diffusion for initial setup...${NC}"
./setup/docker-run.sh
echo -e "${GREEN}✓ Initial Stable Diffusion setup complete${NC}\n"

echo -e "${YELLOW}Starting Stable Diffusion service...${NC}"
systemctl start stable-diffusion
echo -e "${GREEN}✓ Stable Diffusion service started${NC}\n"

echo -e "${YELLOW}Waiting for Stable Diffusion to start...${NC}"
while true; do
    journalctl -u stable-diffusion -n 50 --no-pager --follow | while read -r line; do
        echo "$line"
        if echo "$line" | grep -q "Running on local URL:.*:7860"; then
            pkill -P $$ journalctl
            exit 0
        fi
    done
    
    # Exit the outer loop if inner loop exited successfully
    if [ $? -eq 0 ]; then
        break
    fi
done
echo -e "${GREEN}✓ Stable Diffusion is now running${NC}\n"

# Set up the clockross environment
echo -e "${YELLOW}Step 7: Setting up Python environment for ClockRoss...${NC}"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
chown -R clockross:clockross /opt/clockross
echo -e "${GREEN}✓ Python environment ready${NC}\n"

# Set up the monitor configuration
echo -e "${YELLOW}Step 8: Configuring monitor settings...${NC}"
cp setup/10-monitor.conf /etc/X11/xorg.conf.d/10-monitor.conf
echo -e "${GREEN}✓ Monitor configuration applied${NC}\n"

# Configure sudoers for clockross user
echo -e "${YELLOW}Step 9: Configuring user permissions...${NC}"
echo "clockross ALL=(ALL) NOPASSWD: /usr/sbin/shutdown" > /etc/sudoers.d/clockross
chmod 440 /etc/sudoers.d/clockross
echo -e "${GREEN}✓ User permissions set${NC}\n"

# Set the default target to multi-user.target
echo -e "${YELLOW}Step 10: Setting system target...${NC}"
systemctl set-default multi-user.target
echo -e "${GREEN}✓ System target configured${NC}\n"

# Write a finish-setup.sh script that runs 1 second after this script finishes, does init 3 and starts the clockross service
echo -e "${YELLOW}Step 11: Preparing system restart...${NC}"
echo -e "${GREEN}✓ Setup complete${NC}\n"

echo -e "${BLUE}ClockRoss setup completed successfully!${NC}"
echo -e "${YELLOW}Restarting the system in 5 seconds...${NC}"
sleep 5
reboot
