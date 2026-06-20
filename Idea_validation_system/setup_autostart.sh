#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# setup_autostart.sh — One-time Jetson setup script
#
# Run this ONCE on the Jetson to:
#   1. Add biswa to the docker group (no more sudo password for docker)
#   2. Enable mDNS so the Jetson is accessible as biswa.local on LAN
#   3. Install a systemd service for auto-start on boot
#
# Usage (on Jetson):
#   chmod +x setup_autostart.sh && ./setup_autostart.sh
# ─────────────────────────────────────────────────────────────────────────────

set -e
APP_DIR="$HOME/Idea_validation_system"
SERVICE_NAME="idea-lab"
JETSON_HOSTNAME=$(hostname)

echo "============================================================"
echo "⚙️  ThynxAI Idea Lab — One-Time Setup"
echo "   Jetson hostname: $JETSON_HOSTNAME"
echo "============================================================"
echo ""

# ── Step 1: Add user to docker group ─────────────────────────────────────────
# This removes the need for 'sudo' in front of every docker command.
# Takes effect after next login / reboot.
echo "🐳 Adding $USER to docker group..."
sudo usermod -aG docker "$USER"
echo "✅ Docker group added (takes effect after reboot)"

# ── Step 2: Enable mDNS (Avahi) for biswa.local hostname ─────────────────────
echo ""
echo "📡 Checking mDNS (Avahi) service..."
if ! command -v avahi-daemon &>/dev/null; then
    echo "   Installing avahi-daemon..."
    sudo apt-get install -y avahi-daemon avahi-utils -q
fi

sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon
echo "✅ mDNS enabled — Jetson accessible as: ${JETSON_HOSTNAME}.local"
echo "   From your Mac: http://${JETSON_HOSTNAME}.local:8501"

# ── Step 3: Create systemd service ───────────────────────────────────────────
echo ""
echo "🔧 Installing systemd auto-start service..."

sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null << EOF
[Unit]
Description=ThynxAI Idea Lab (LLM + Streamlit)
Documentation=https://github.com/inventor-biswa/EdgeAi_jetson
After=network-online.target docker.service
Wants=network-online.target docker.service
# Give Docker and GPU time to fully initialize
StartLimitIntervalSec=120
StartLimitBurst=3

[Service]
Type=simple
User=$USER
Group=docker
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/start_idea_app.sh
# Restart if it crashes, but not if we manually stop it
Restart=on-failure
RestartSec=15
# Log to journald (view with: journalctl -u idea-lab -f)
StandardOutput=journal
StandardError=journal
# Give the model 5 minutes to load before systemd gives up
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}.service
echo "✅ Service installed and enabled"

# ── Step 4: Update start_idea_app.sh to not use sudo for docker ──────────────
# After adding to docker group (+ reboot), docker works without sudo.
# Patch the script to use 'docker' instead of 'sudo docker'.
echo ""
echo "🔧 Patching start_idea_app.sh to remove sudo from docker commands..."
sed -i 's/sudo docker/docker/g' "$APP_DIR/start_idea_app.sh"
echo "✅ Patched"

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "============================================================"
echo "✅ Setup complete! REBOOT the Jetson now:"
echo "   sudo reboot"
echo ""
echo "After reboot, the app starts automatically."
echo ""
echo "🌐 Access the app from any device on your network:"
echo "   http://${JETSON_HOSTNAME}.local:8501"
echo ""
echo "   No SSH tunnel needed!"
echo ""
echo "📋 Useful commands:"
echo "   View logs:   journalctl -u $SERVICE_NAME -f"
echo "   Stop app:    sudo systemctl stop $SERVICE_NAME"
echo "   Start app:   sudo systemctl start $SERVICE_NAME"
echo "   Restart app: sudo systemctl restart $SERVICE_NAME"
echo "   Status:      sudo systemctl status $SERVICE_NAME"
echo "============================================================"
