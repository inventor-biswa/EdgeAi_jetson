# 🚀 ThynxAI Idea Lab v2.0 — Secure Offline Edition

An AI-powered system that analyzes startup ideas and generates detailed evaluation reports, pitch decks, and roadmaps.

**v2.0 Update:** The application has been completely redesigned to run **100% offline and locally on private edge hardware**. No cloud API keys, no external database connections, and completely private.

---

## 📌 What it Does

1. Takes a startup idea as input.
2. Collects detailed founder information through a conversational chat interface.
3. Generates intelligent adaptive follow-up questions based on the idea and founder profile.
4. Analyzes the idea across 8 structured dimensions using a local LLM.
5. Generates a detailed evaluation report (JSON + Markdown).
6. **[NEW]** Instantly generates a structured PowerPoint Pitch Deck (`.pptx`).
7. **[NEW]** Provides an offline floating chat mentor widget to answer follow-up questions about your specific business idea.

---

## 🧩 Project Structure

```
Idea_validation_system/
├── frontend/               # Next.js React Web Application (Port 3000)
├── api/
│   └── main.py             # FastAPI Backend Server (Port 8000)
├── prompts.py              # System prompts for the local LLM
├── analyzer.py             # Logic for communicating with local llama.cpp server
├── ppt.py                  # Programmatic PowerPoint (.pptx) generation
├── start_idea_app.sh       # Main launcher script (managed by systemd)
├── jetson_analyses.db      # Local SQLite database storing all sessions
└── idea_env/               # Python virtual environment
```

---

## ⚙️ Architecture & Tech Stack

This project is built explicitly for private edge hardware, focusing on privacy and local inference:

- **Frontend:** Next.js, React, Vanilla CSS, Framer Motion (Glassmorphic UI)
- **Backend:** FastAPI, Python, SQLite3
- **AI Engine:** `llama.cpp` Server (Dockerized, using NVIDIA runtime)
- **LLM Model:** local quantized instruct model (`.gguf`)
- **Deployment:** `systemd` autostart manager

---

## 🚀 How to Run

Because the system is configured to boot automatically on the Jetson, you do not need to manually start it! 

### Accessing the App
As soon as you turn on the Jetson, the LLM and web servers boot in the background. Simply connect to the same WiFi network and visit:
- **`http://biswa.local:3000`**
- Or using the IP: `http://<jetson-ip>:3000`

### Managing the Background Service
The application runs as a systemd service (`idea-lab.service`). You can control it via SSH:

```bash
# Check the status of the app
systemctl status idea-lab.service

# View the live logs (FastAPI & Next.js)
journalctl -u idea-lab.service -f

# Restart the application
sudo systemctl restart idea-lab.service

# Stop the application entirely
sudo systemctl stop idea-lab.service
```

### Viewing LLM Container Logs
If you need to verify the GPU allocation or token generation speed of the offline model:
```bash
docker logs -f llm-server
```

---

## 📊 Analysis Output

After running an idea through the system, you can instantly download:
- **JSON Report:** Raw structured data.
- **Markdown Report:** A clean, human-readable text document.
- **Pitch Deck (.pptx):** A fully structured 6-slide PowerPoint presentation generated natively without external templates.

*Built entirely for offline edge computing on private, on-device hardware.*