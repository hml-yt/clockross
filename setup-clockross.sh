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

# Create virtual environment
echo -e "${YELLOW}Step 2: Setting up Python environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
echo -e "${GREEN}✓ Python environment ready${NC}\n"

# Create models directory and download models
echo -e "${YELLOW}Step 3: Downloading AI models...${NC}"
mkdir -p models

# Define model URLs
VAE_URL="https://huggingface.co/stabilityai/sd-vae-ft-mse-original/resolve/main/vae-ft-mse-840000-ema-pruned.safetensors"
CONTROLNET_URL="https://huggingface.co/nolanaatama/models/resolve/main/control_v11f1e_sd15_tile_fp16.safetensors"
BASE_MODEL_URL="https://civitai.com/api/download/models/115588?type=Model&format=SafeTensor&size=full&fp=fp16"

# Download models
echo "Downloading VAE model..."
wget -O models/vae-ft-mse-840000-ema-pruned.safetensors "$VAE_URL"

echo "Downloading ControlNet model..."
wget -O models/control_v11f1e_sd15_tile.safetensors "$CONTROLNET_URL"

echo "Downloading base model..."
wget -O models/abstractPhoto_abcevereMix.safetensors "$BASE_MODEL_URL"
echo -e "${GREEN}✓ Models downloaded successfully${NC}\n"

# Disable screensaver and screen blanking
echo -e "${YELLOW}Step 4: Configuring display settings...${NC}"
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

# Create systemd service
echo -e "${YELLOW}Step 5: Setting up system service...${NC}"
cat > /etc/systemd/system/clockross.service << EOL
[Unit]
Description=ClockRoss AI Clock
After=network.target

[Service]
Type=simple
User=$SUDO_USER
WorkingDirectory=$INSTALL_DIR
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/$SUDO_USER/.Xauthority
ExecStart=$INSTALL_DIR/venv/bin/python main.py
Restart=always
RestartSec=3

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
echo -e "${YELLOW}Step 6: Configuring user permissions...${NC}"
echo "$SUDO_USER ALL=(ALL) NOPASSWD: /sbin/shutdown" > /etc/sudoers.d/clockross
chmod 440 /etc/sudoers.d/clockross
echo -e "${GREEN}✓ User permissions set${NC}\n"

# Set the default target to multi-user.target
echo -e "${YELLOW}Step 7: Setting system target...${NC}"
systemctl set-default multi-user.target
echo -e "${GREEN}✓ System target configured${NC}\n"

echo -e "${BLUE}ClockRoss setup completed successfully!${NC}"
echo -e "${YELLOW}The system will start in multi-user mode after reboot.${NC}"
echo -e "${YELLOW}The clock will start automatically on boot.${NC}"
echo -e "${YELLOW}Restarting in 5 seconds...${NC}"
sleep 5
reboot
