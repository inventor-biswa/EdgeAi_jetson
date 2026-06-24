# Dev Workflow (alongside the `idea-lab` auto-start service)

`idea-lab.service` is enabled and auto-starts the full production stack on every
boot (LLM container → FastAPI on :8000 with no `--reload` → Next.js production
build + `npm start` on :3000). None of that watches files or hot-reloads, so
editing code requires pausing it first.

Two things shape this workflow:
- **RAM is the real constraint, not just systemd.** The Jetson has 7.3GB total,
  and a single 7B Q4 model already uses ~70% of it. There's only enough
  headroom for one model loaded at a time — don't try to run a second LLM
  alongside production.
- **Backgrounding over a one-off SSH command does not survive disconnects on
  this box.** Tested directly: even `setsid` + `nohup` + `disown` got killed
  the instant the SSH session closed, because this Ubuntu setup tears down
  everything in the login session's cgroup on disconnect. Use `tmux` for
  anything that needs to keep running after you disconnect.

---

## 0. Where everything lives

There are **two copies** of this project: your local Mac checkout (where you
edit) and the deployed copy on the Jetson (where it actually runs). Nothing
syncs automatically between them — every change has to be copied over by hand
(or via `git pull` on the Jetson, if you're committing/pushing instead of
copying files directly).

| | Path |
|---|---|
| Local repo (Mac, this checkout) | `/Users/thynxai/thynx/Jetson/Idea_validation_system/` |
| Deployed copy (Jetson) | `/home/biswa/Idea_validation_system/` (user `biswa`, host `192.168.1.32`) |
| SSH helper (Mac → Jetson, password auto-filled) | `/Users/thynxai/thynx/Jetson/ssh_sudo2.exp "<remote command>"` |
| SCP helper (copy file/dir Mac → Jetson) | `/Users/thynxai/thynx/Jetson/scp_cmd.exp <local path> <remote path>` |

Both helper scripts live one level **above** this project, in `~/thynx/Jetson/`,
not inside `Idea_validation_system/`.

### What's inside the project, and what it controls

| Path | What it is | Needs after editing |
|---|---|---|
| `api/main.py` | FastAPI routes (`/api/validate`, `/api/chat`, `/health`, etc.) | Restart backend process — no build step (Python) |
| `analyzer.py` | Core LLM call logic (`call_gemini`), JSON parsing/repair, prompts wiring | Restart backend process |
| `prompts.py` | The actual prompt text sent to the model | Restart backend process |
| `websearch.py` | Offline market-research context lookup | Restart backend process |
| `database.py` | SQLite read/write for saved analyses | Restart backend process |
| `report.py`, `ppt.py` | Report/PPTX export generation | Restart backend process |
| `frontend/pages/`, `frontend/components/`, `frontend/lib/` | Next.js UI, API client, hooks | **Rebuild** (`npm run build`) then restart |
| `.env` (on the Jetson only — not in git) | `LLM_API_URL`, `LLM_MODEL`, `SQLITE_DB_PATH`, etc. | Restart backend process |
| `~/models/*.gguf` (on the Jetson, outside this repo) | The actual LLM weight files | Restart the `llm-server` Docker container (not the backend) |
| `jetson_analyses.db` (on the Jetson, repo root) | SQLite database of saved analyses — **do not delete/overwrite when deploying**, it's not part of the code | Nothing — it's data, not code |
| `start_idea_app.sh` | The production launcher; what `idea-lab.service` runs | Restart the whole service (`systemctl restart idea-lab`) |
| `setup_autostart.sh` | One-time installer for the systemd unit — you won't normally touch this | `sudo systemctl daemon-reload` + re-run if ever edited |
| `/etc/systemd/system/idea-lab.service` (on the Jetson, not in this repo) | The actual systemd unit definition | `sudo systemctl daemon-reload` if ever edited |

---

## 1. Pause production before developing

```bash
/Users/thynxai/thynx/Jetson/ssh_sudo2.exp "sudo systemctl stop idea-lab"
# ...do dev work (sections 2-3 below)...
/Users/thynxai/thynx/Jetson/ssh_sudo2.exp "sudo systemctl start idea-lab"
```

This frees ports 8000/3000 and stops the production stack competing for RAM.
Only `sudo systemctl disable idea-lab` too if doing a multi-day dev stretch
spanning reboots — otherwise leave it enabled, so an unplanned reboot still
self-heals back to showcase-ready.

## 2. Run dev servers inside `tmux`

```bash
ssh biswa@192.168.1.32
tmux new -s dev

# pane 1 — backend with auto-reload on save:
cd ~/Idea_validation_system
idea_env/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# pane 2 (tmux split, Ctrl+B %) — frontend with hot reload:
cd ~/Idea_validation_system/frontend
npm run dev -- --port 3000
```

Both already exist as-is (`frontend/package.json`'s `"dev": "next dev"`
script; `--reload` is even mentioned in `api/main.py`'s own docstring) — just
use them instead of the production commands. This reuses the **same
already-running `llm-server` container**, so code iteration doesn't load a
second model into memory.

Detach with `Ctrl+B D`. Reattach anytime — even after fully closing the SSH
session — with:

```bash
tmux attach -t dev
```

While the dev `uvicorn --reload` / `next dev` are running this way, you can
edit files **directly on the Jetson** (e.g. via `nano`/`vim` over the same SSH
session, or mount the directory in VS Code Remote-SSH) and see changes
reflected immediately — no copy/rebuild step needed during this loop. The
copy-from-Mac steps in section 3 are for when you've been editing the **local**
checkout instead and need to push those edits over.

## 3. Making a change and getting it onto the Jetson

Pick the row that matches what you changed locally, then copy it over.

### Backend Python file (`api/main.py`, `analyzer.py`, `prompts.py`, `websearch.py`, `database.py`, `report.py`, `ppt.py`)

```bash
# from the Mac, in this repo:
/Users/thynxai/thynx/Jetson/scp_cmd.exp <local-file-path> /home/biswa/Idea_validation_system/<same-relative-path>

# if a dev uvicorn --reload is already running in tmux: nothing else to do, it reloads itself.
# if you're testing against the production service instead:
/Users/thynxai/thynx/Jetson/ssh_sudo2.exp "sudo systemctl restart idea-lab"
```

No build step — Python is interpreted, so the copy alone is enough once
something (dev `--reload` or a restart) picks the new file up.

### Frontend file (`frontend/pages/*`, `frontend/components/*`, `frontend/lib/*`)

```bash
/Users/thynxai/thynx/Jetson/scp_cmd.exp <local-file-path> /home/biswa/Idea_validation_system/<same-relative-path>

# if a dev `next dev` is already running in tmux: nothing else to do, it hot-reloads.
# if you're testing against the production service instead, it MUST be rebuilt —
# production serves the static .next build, not live source:
/Users/thynxai/thynx/Jetson/ssh_sudo2.exp "cd /home/biswa/Idea_validation_system/frontend && npm run build"
/Users/thynxai/thynx/Jetson/ssh_sudo2.exp "sudo systemctl restart idea-lab"
```

### `.env` / config change (`LLM_API_URL`, `LLM_MODEL`, `SQLITE_DB_PATH`, ...)

Edit `.env` directly on the Jetson (it's not checked into git, so there's
nothing to copy from the Mac):

```bash
/Users/thynxai/thynx/Jetson/ssh_sudo2.exp "nano /home/biswa/Idea_validation_system/.env"
/Users/thynxai/thynx/Jetson/ssh_sudo2.exp "sudo systemctl restart idea-lab"
```

### Swapping the loaded LLM model

Only one model fits in RAM at a time, so this is swap-not-add. Run on the
Jetson (model files live outside this repo, in `~/models/`):

```bash
docker stop llm-server
docker run -d --rm --name llm-server --runtime=nvidia --network host \
    -v ~/models:/models \
    ghcr.io/nvidia-ai-iot/llama_cpp:latest-jetson-orin \
    llama-server -m "/models/<your-model>.gguf" --ctx-size 8196 \
    --alias my_model --n-gpu-layers 999
```

Keep `--alias my_model` so `.env`'s `LLM_MODEL` never needs to change — the
backend only talks to `LLM_API_URL` (an OpenAI-compatible
`/v1/chat/completions` endpoint, see `analyzer.py:40-43`) and doesn't care
which model is actually behind it. No backend/frontend restart needed — same
URL, same alias, just different weights behind it.

Check readiness the same way `start_idea_app.sh` does:

```bash
curl http://127.0.0.1:8080/health      # wait for {"status":"ok"}
curl http://127.0.0.1:8080/v1/models   # fallback check, ~90s+ for a 7B model
```

### Multiple files changed at once

Use `scp_cmd.exp` with a directory instead of a single file (it already
passes `-r` to `scp`):

```bash
/Users/thynxai/thynx/Jetson/scp_cmd.exp frontend/components /home/biswa/Idea_validation_system/frontend/components
```

Then follow whichever rebuild/restart step applies to what you copied
(backend-only → just restart; any frontend files → rebuild then restart).

## 4. Returning to showcase mode

Whatever path you took above, the final state to confirm before walking away:

```bash
/Users/thynxai/thynx/Jetson/ssh_sudo2.exp "sudo systemctl start idea-lab"   # add 'enable' too if it had been disabled
/Users/thynxai/thynx/Jetson/ssh_sudo2.exp "curl -s http://127.0.0.1:8000/health"
```

Expect `{"status":"ok","llm":"ready"}`. If it says `"llm":"warming_up"`, the
LLM container just (re)started and needs its ~90s model-load window — wait
and re-check rather than assuming something's broken.

If a dev `tmux` session (section 2) is still running, you don't have to kill
it — just make sure `idea-lab.service` is started and bound to the same ports
(8000/3000), since whichever one starts last will fail to bind if the other
is still holding the port. Easiest to fully stop the tmux dev servers
(`Ctrl+C` in each pane) before starting `idea-lab` back up.
