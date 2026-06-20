#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# deploy_to_jetson.sh — Mac-side deployment script
#
# Copies the Idea_validation_system to the Jetson Orin Nano and starts the app.
# Uses the existing scp_cmd.exp and ssh_cmd.exp scripts.
#
# NOTE: ssh_cmd.exp only handles single-line commands (it passes $argv 0 to ssh).
#       All multi-line SSH steps are split into separate single-line calls here.
#
# Run this FROM YOUR MAC:
#   chmod +x deploy_to_jetson.sh
#   ./deploy_to_jetson.sh
# ─────────────────────────────────────────────────────────────────────────────

set -e

JETSON_IP="192.168.1.56"
JETSON_USER="biswa"
JETSON_DEST="/home/biswa/Idea_validation_system"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCP_SCRIPT="$SCRIPT_DIR/scp_cmd.exp"
SSH_SCRIPT="$SCRIPT_DIR/ssh_cmd.exp"
APP_DIR="$SCRIPT_DIR/Idea_validation_system"

echo "============================================================"
echo "🚀 Deploying Idea Validation System to Jetson"
echo "   Target: $JETSON_USER@$JETSON_IP:$JETSON_DEST"
echo "============================================================"
echo ""

# ── Step 1: Copy project files (exclude .git folder to avoid junk) ────────────
echo "📦 Copying project files to Jetson..."

# Use rsync if available, otherwise fall back to scp
if command -v rsync &>/dev/null; then
    rsync -avz --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
        -e "sshpass -p biswa ssh -o StrictHostKeyChecking=no" \
        "$APP_DIR/" "$JETSON_USER@$JETSON_IP:$JETSON_DEST/"
else
    # scp fallback — copies everything including .git (harmless but slow)
    "$SCP_SCRIPT" "$APP_DIR" "/home/$JETSON_USER/"
fi
echo "✅ Files copied"

# ── Step 2: Make startup script executable ────────────────────────────────────
echo "🔑 Setting executable permissions..."
"$SSH_SCRIPT" "chmod +x $JETSON_DEST/start_idea_app.sh"
echo "✅ Permissions set"

# ── Step 3: Create venv if it does not exist (single-line each) ───────────────
echo "🐍 Setting up Python virtual environment..."
"$SSH_SCRIPT" "test -d $JETSON_DEST/idea_env || python3 -m venv $JETSON_DEST/idea_env"
echo "✅ Venv ready"

# ── Step 4: Upgrade pip ───────────────────────────────────────────────────────
echo "⬆️  Upgrading pip..."
"$SSH_SCRIPT" "$JETSON_DEST/idea_env/bin/pip install --upgrade pip -q"
echo "✅ pip upgraded"

# ── Step 5: Install requirements ──────────────────────────────────────────────
echo "📦 Installing Python dependencies (this may take a minute)..."
"$SSH_SCRIPT" "$JETSON_DEST/idea_env/bin/pip install -r $JETSON_DEST/requirements.txt -q"
echo "✅ Dependencies installed"

# ── Step 6: Create .env if missing ───────────────────────────────────────────
echo "📄 Checking .env..."
"$SSH_SCRIPT" "test -f $JETSON_DEST/.env || cp $JETSON_DEST/.env.example $JETSON_DEST/.env"
echo "✅ .env ready"

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "============================================================"
echo "✅ Deployment complete!"
echo ""
echo "▶  To start the app, SSH into the Jetson and run:"
echo "   cd ~/Idea_validation_system && ./start_idea_app.sh"
echo ""
echo "   Or from this Mac:"
echo "   $SSH_SCRIPT 'cd ~/Idea_validation_system && ./start_idea_app.sh'"
echo ""
echo "   Then open in your Mac browser:"
echo "   http://$JETSON_IP:8501"
echo "============================================================"
