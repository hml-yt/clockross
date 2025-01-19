#!/bin/bash

# Color definitions
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting ClockRoss Setup...${NC}\n"

# Clone repository
echo -e "${YELLOW}Step 1: Cloning ClockRoss repository...${NC}"
INSTALL_DIR="/opt/clockross"
git clone https://github.com/hml-yt/clockross.git $INSTALL_DIR
cd $INSTALL_DIR
chown -R $SUDO_USER:$SUDO_USER $INSTALL_DIR
echo -e "${GREEN}✓ Repository cloned successfully${NC}\n"

# Install system dependencies
echo -e "${YELLOW}Step 2: Installing system dependencies...${NC}"
apt-get update
apt-get install -y tesseract-ocr libtesseract-dev libopenblas-base libatlas3-base
echo -e "${GREEN}✓ System dependencies installed${NC}\n"

# Create virtual environment
echo -e "${YELLOW}Step 3: Setting up Python environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
echo -e "${GREEN}✓ Python environment ready${NC}\n"

# Create models directory and download models
echo -e "${YELLOW}Step 4: Downloading AI models...${NC}"
mkdir -p models

# Define model URLs
VAE_URL="https://huggingface.co/stabilityai/sd-vae-ft-mse-original/resolve/main/vae-ft-mse-840000-ema-pruned.safetensors"
CONTROLNET_URL="https://huggingface.co/nolanaatama/models/resolve/main/control_v11f1e_sd15_tile_fp16.safetensors"
ABSTRACT_MODEL_URL="https://civitai.com/api/download/models/115588?type=Model&format=SafeTensor&size=full&fp=fp16&token=e73d59d536fa858d3dc918289851d39f"
REV_ANIMATED_URL="https://civitai.com/api/download/models/425083?type=Model&format=SafeTensor&size=full&fp=fp16&token=e73d59d536fa858d3dc918289851d39f"

# Download models
echo "Downloading VAE model..."
wget -O models/vae-ft-mse-840000-ema-pruned.safetensors "$VAE_URL"

echo "Downloading ControlNet model..."
wget -O models/control_v11f1e_sd15_tile.safetensors "$CONTROLNET_URL"

echo "Downloading Abstract Photo model..."
wget -O models/abstractPhoto_abcevereMix.safetensors "$ABSTRACT_MODEL_URL"

echo "Downloading Rev Animated model..."
wget -O models/revAnimated_v2Rebirth.safetensors "$REV_ANIMATED_URL"
echo -e "${GREEN}✓ Models downloaded successfully${NC}\n"

# Disable screensaver and screen blanking
echo -e "${YELLOW}Step 5: Configuring display settings...${NC}"
# Try GNOME settings first
if command -v gsettings &> /dev/null; then
    gsettings set org.gnome.desktop.session idle-delay 0
    gsettings set org.gnome.desktop.screensaver lock-enabled false
    gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'
fi
# X11 settings
if command -v xset &> /dev/null; then
    xset s off
    xset -dpms
    xset s noblank
fi
echo -e "${GREEN}✓ Display settings configured${NC}\n"

# Configure X11 monitor settings
echo -e "${YELLOW}Step 5a: Creating X11 monitor configuration...${NC}"
cat > /etc/X11/xorg.conf.d/10-monitor.conf << EOL
Section "ServerFlags"
	Option "BlankTime" "0"
	Option "StandbyTime" "0"
	Option "SuspendTime" "0"
	Option "OffTime" "0"
EndSection
EOL
chmod 644 /etc/X11/xorg.conf.d/10-monitor.conf
echo -e "${GREEN}✓ Monitor configuration created${NC}\n"

# Create systemd service
echo -e "${YELLOW}Step 6: Setting up system service...${NC}"
cat > /etc/systemd/system/clockross.service << EOL
[Unit]
Description=Clock App
After=network.target stable-diffusion.service

[Service]
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/$SUDO_USER/.Xauthority
User=$SUDO_USER
Group=$SUDO_USER
WorkingDirectory=$INSTALL_DIR
ExecStartPre=/bin/bash -c "/usr/bin/X :0 -quiet &"
ExecStart=/bin/bash -c "source $INSTALL_DIR/venv/bin/activate && python main.py"
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

# Set proper permissions
chmod 644 /etc/systemd/system/clockross.service

# Enable and start the service
systemctl daemon-reload
systemctl enable clockross.service
echo -e "${GREEN}✓ System service configured${NC}\n"

# Configure sudoers for shutdown/restart
echo -e "${YELLOW}Step 7: Configuring user permissions...${NC}"
echo "$SUDO_USER ALL=(ALL) NOPASSWD: /sbin/shutdown" > /etc/sudoers.d/clockross
chmod 440 /etc/sudoers.d/clockross
echo -e "${GREEN}✓ User permissions set${NC}\n"

# Set the default target to multi-user.target
echo -e "${YELLOW}Step 8: Setting system target...${NC}"
systemctl set-default multi-user.target
echo -e "${GREEN}✓ System target configured${NC}\n"

echo -e "${BLUE}ClockRoss setup completed successfully!${NC}"
echo -e "${YELLOW}The system will start in multi-user mode after reboot.${NC}"
echo -e "${YELLOW}The clock will start automatically on boot.${NC}"
echo -e "${YELLOW}Restarting in 5 seconds...${NC}"
sleep 5
reboot
