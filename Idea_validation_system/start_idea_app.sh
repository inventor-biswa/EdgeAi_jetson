#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# start_idea_app.sh — Jetson startup script for Idea Validation System
#
# Run this script ON THE JETSON to:
#   1. Check if LLM server is already running (avoids double-starting Docker)
#   2. Start Nemotron LLM server if not running
#   3. Wait for it to be ready
#   4. Activate the Python venv
#   5. Launch Streamlit UI (accessible from Mac at http://192.168.1.56:8501)
#
# Usage (on Jetson):
#   chmod +x start_idea_app.sh
#   ./start_idea_app.sh
# ─────────────────────────────────────────────────────────────────────────────

set -e

APP_DIR="$HOME/Idea_validation_system"
VENV_DIR="$APP_DIR/idea_env"
LLM_CONTAINER="llm-server"
LLM_URL="http://127.0.0.1:8080/health"
LLM_STARTUP_WAIT=90   # seconds — 4B model needs time to load from HF cache into GPU

echo "============================================================"
echo "🚀 ThynxAI Idea Lab — Jetson Offline Launcher"
echo "============================================================"

# ── Step 1: Find the local GGUF model ────────────────────────────────────────
# Use the model at ~/models/ — bypasses HuggingFace entirely (true offline).
# Prefers Qwen2.5-7B if present, then falls back to any other .gguf file found.
echo ""
echo "🔍 Looking for local GGUF model..."

MODEL_DIR="$HOME/models"
PREFERRED_MODEL="$MODEL_DIR/Qwen2.5-7B-Instruct-Q4_K_M.gguf"

if [ -f "$PREFERRED_MODEL" ]; then
    MODEL_PATH="$PREFERRED_MODEL"
else
    # Find any .gguf in ~/models/
    MODEL_PATH=$(find "$MODEL_DIR" -name "*.gguf" 2>/dev/null | head -1)
fi

if [ -z "$MODEL_PATH" ]; then
    echo "❌ No GGUF model found in $MODEL_DIR"
    echo ""
    echo "   Download one first — run on the Jetson:"
    echo "   wget -O ~/models/Qwen2.5-7B-Instruct-Q4_K_M.gguf \\"
    echo "     'https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF/resolve/main/Qwen2.5-7B-Instruct-Q4_K_M.gguf'"
    exit 1
fi

echo "✅ Using model: $(basename $MODEL_PATH)"
MODEL_FILENAME=$(basename "$MODEL_PATH")

# ── Step 2: Check / Start LLM Server ─────────────────────────────────────────
echo ""
echo "🧠 Checking LLM server..."

if docker ps --format '{{.Names}}' | grep -q "^${LLM_CONTAINER}$"; then
    echo "✅ LLM server already running (${LLM_CONTAINER})"
else
    echo "⏳ Starting LLM server with local model..."
    docker stop "$LLM_CONTAINER" > /dev/null 2>&1 || true
    docker run -d --rm \
        --name "$LLM_CONTAINER" \
        --runtime=nvidia \
        --network host \
        -v "$MODEL_DIR:/models" \
        ghcr.io/nvidia-ai-iot/llama_cpp:latest-jetson-orin \
        llama-server \
        -m "/models/$MODEL_FILENAME" \
        --ctx-size 8196 \
        --alias my_model \
        --n-gpu-layers 999

    echo "⏳ Waiting ${LLM_STARTUP_WAIT}s for model to load into GPU memory..."
    sleep "$LLM_STARTUP_WAIT"
fi

# ── Step 2: Health check ──────────────────────────────────────────────────────
# Strategy:
#   1. Try /health — matches "status":"ok" OR "status": "ok" (with or without space)
#   2. Fallback: try /v1/models — this endpoint always returns 200 when server is up
#      (confirmed working in jetragv1/query.py)
echo "🔍 Verifying LLM server health..."
MAX_CHECKS=20   # 20 × 5s = 100s extra wait after initial sleep

for i in $(seq 1 $MAX_CHECKS); do
    # Try /health first — use flexible grep to handle "status":"ok" or "status": "ok"
    HEALTH_BODY=$(curl -s --max-time 5 "$LLM_URL" 2>/dev/null || echo "")

    if echo "$HEALTH_BODY" | grep -qE '"status"\s*:\s*"ok"'; then
        echo "✅ LLM server is ready! (health endpoint)"
        break
    elif echo "$HEALTH_BODY" | grep -qE '"status"\s*:\s*"loading'; then
        echo "   Still loading model into GPU... ($i/$MAX_CHECKS)"
    else
        # Fallback: try /v1/models — lighter endpoint, always works when server is up
        MODELS_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 \
            "http://127.0.0.1:8080/v1/models" 2>/dev/null || echo "000")

        if [ "$MODELS_CODE" = "200" ]; then
            echo "✅ LLM server is ready! (/v1/models responded)"
            break
        else
            echo "   Waiting for server to respond... ($i/$MAX_CHECKS) [health: '${HEALTH_BODY:0:40}', models: $MODELS_CODE]"
        fi
    fi

    if [ "$i" -eq "$MAX_CHECKS" ]; then
        echo ""
        echo "❌ LLM server did not respond after $(( LLM_STARTUP_WAIT + MAX_CHECKS * 5 ))s total."
        echo "   Run this to check: docker logs $LLM_CONTAINER"
        echo "   Or test manually:  curl http://127.0.0.1:8080/health"
        echo "                      curl http://127.0.0.1:8080/v1/models"
        exit 1
    fi
    sleep 5
done

# ── Step 3: Set up Python venv (first run only) ───────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    echo ""
    echo "📦 First run — creating Python virtual environment..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip -q
    pip install -r "$APP_DIR/requirements.txt" -q
    echo "✅ Python environment ready"
else
    source "$VENV_DIR/bin/activate"
fi

# ── Step 4: Create .env if missing ───────────────────────────────────────────
if [ ! -f "$APP_DIR/.env" ]; then
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    echo "📄 Created .env from template"
fi

# ── Step 5: Set up Node.js frontend (first run only) ─────────────────────────
FRONTEND_DIR="$APP_DIR/frontend"
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo ""
    echo "📦 First run — installing Next.js dependencies..."
    cd "$FRONTEND_DIR"
    npm install -q
    echo "✅ Frontend dependencies installed"
fi

# Build Next.js production bundle if not already built
if [ ! -d "$FRONTEND_DIR/.next/static" ]; then
    echo ""
    echo "🏗️  Building Next.js frontend for production..."
    cd "$FRONTEND_DIR"
    npm run build
    echo "✅ Frontend build complete"
fi

# Detect actual LAN IP dynamically (avoids hardcoded IP being wrong)
cd "$APP_DIR"
LAN_IP=$(hostname -I 2>/dev/null | tr ' ' '\n' | grep '^192\.168\.' | head -1)
LAN_IP=${LAN_IP:-"(run 'hostname -I' to find IP)"}
HOSTNAME=$(hostname)

# Ensure avahi/mDNS is running so biswa.local works on LAN
# Avahi is usually started by systemd automatically
if ! systemctl is-active --quiet avahi-daemon 2>/dev/null; then
    echo "Warning: avahi-daemon is not active."
fi

echo ""
echo "============================================================"
echo "🚀 ThynxAI Idea Lab v2.0 — FastAPI + Next.js"
echo ""
echo "   📱 From ANY device on your WiFi:"
echo "      http://${LAN_IP}:3000     ← Main App (Next.js)"
echo "      http://${HOSTNAME}.local:3000"
echo ""
echo "   🔌 Backend API (FastAPI):"
echo "      http://${LAN_IP}:8000/docs"
echo ""
echo "   💻 Locally on Jetson:"
echo "      http://localhost:3000"
echo "   Press Ctrl+C to stop both servers"
echo "============================================================"
echo ""

# ── Launch FastAPI backend ────────────────────────────────────────────────────
echo "🔌 Starting FastAPI backend on port 8000..."
cd "$APP_DIR"
uvicorn api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --log-level warning &
FASTAPI_PID=$!

# Brief pause to let uvicorn bind
sleep 2

# ── Launch Next.js frontend ───────────────────────────────────────────────────
echo "🌐 Starting Next.js frontend on port 3000..."
cd "$FRONTEND_DIR"

# Inject the runtime API URL so the browser can find FastAPI via LAN IP
NEXT_PUBLIC_API_URL="http://${LAN_IP}:8000" npm start -- --port 3000 &
NEXT_PID=$!

# ── Graceful shutdown on Ctrl+C ───────────────────────────────────────────────
trap "echo ''; echo '🛑 Stopping ThynxAI...'; kill $FASTAPI_PID $NEXT_PID 2>/dev/null; exit 0" SIGINT SIGTERM

# Keep script alive
wait $NEXT_PID
