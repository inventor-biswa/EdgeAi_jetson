"""
api/main.py — FastAPI backend for ThynxAI Idea Lab
Replaces Streamlit app.py — all Python AI logic is unchanged.

Run with:
    uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
"""

import sys
import os

# Ensure parent directory is on path so we can import existing modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import requests
from io import BytesIO
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from analyzer import (
    validate_input,
    generate_single_question,
    analyze_idea,
    grade_output,
    generate_readiness_tips,
    generate_pitch_slides,
)
from report import save_json, save_markdown
from database import save_analysis, update_analysis_tips
from websearch import get_search_context
from ppt import generate_ppt
from analyzer import LLM_API_URL

# Base URL of the llama-server itself (e.g. http://127.0.0.1:8080), derived
# from the chat-completions endpoint so /health can ping the LLM directly.
LLM_BASE_URL = LLM_API_URL.split("/v1/")[0]


# ─── App Setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="ThynxAI Idea Lab API",
    description="AI-Powered Startup Idea Validator — Offline Edition",
    version="2.0.0",
)

# Allow Next.js frontend to call us (localhost:3000 in dev, same origin in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request / Response Models ────────────────────────────────────────────────

class ValidateRequest(BaseModel):
    idea: str

class QuestionRequest(BaseModel):
    idea: str
    founder_name: str
    founder_data: Dict[str, Any]
    history: List[Dict[str, str]]
    search_context: Optional[Dict[str, Any]] = None

class SearchRequest(BaseModel):
    idea: str
    founder_data: Dict[str, Any]

class AnalyzeRequest(BaseModel):
    idea: str
    founder_name: str
    founder_data: Dict[str, Any]
    followup_qa: List[Dict[str, str]]
    search_context: Optional[Dict[str, Any]] = None

class ReadinessRequest(BaseModel):
    analysis: Dict[str, Any]
    readiness_type: str   # "mvp" or "investment"
    search_context: Optional[Dict[str, Any]] = None

class PptRequest(BaseModel):
    analysis: Dict[str, Any]

class ReportRequest(BaseModel):
    analysis: Dict[str, Any]


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "ok", "service": "ThynxAI Idea Lab API v2.0"}


@app.get("/health")
async def health():
    """Backend is always 'ok' if this responds; llm reflects whether the
    model server is actually reachable (e.g. still warming up after a
    restart, which takes ~90s)."""
    try:
        r = requests.get(f"{LLM_BASE_URL}/health", timeout=2)
        llm_status = "ready" if r.ok else "warming_up"
    except requests.exceptions.RequestException:
        llm_status = "warming_up"
    return {"status": "ok", "llm": llm_status}


# ── Step 1: Validate idea ─────────────────────────────────────────────────────

@app.post("/api/validate")
async def api_validate(req: ValidateRequest):
    """Validates whether the input is a real startup idea."""
    if not req.idea.strip():
        raise HTTPException(status_code=400, detail="Idea cannot be empty.")
    try:
        result = validate_input(req.idea)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Step 2→3 bridge: Market research ─────────────────────────────────────────

@app.post("/api/search")
async def api_search(req: SearchRequest):
    """Runs offline market research — called once after founder profile is done."""
    try:
        context = get_search_context(req.idea, req.founder_data)
        return {"search_context": context}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Step 3: Adaptive questions ────────────────────────────────────────────────

@app.post("/api/question")
async def api_question(req: QuestionRequest):
    """Generates the next adaptive follow-up question for the idea."""
    try:
        question = generate_single_question(
            req.idea,
            req.founder_name,
            req.founder_data,
            req.history,
            req.search_context,
        )
        return {"question": question}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Step 4: Full analysis ─────────────────────────────────────────────────────

@app.post("/api/analyze")
async def api_analyze(req: AnalyzeRequest):
    """
    Runs the full 8-dimension startup analysis.
    Includes up to 3 retries with grade quality check (same as original app.py).
    """
    MAX_RETRIES = 3
    analysis = None
    success = False

    try:
        for attempt in range(MAX_RETRIES):
            analysis = analyze_idea(
                req.idea,
                req.founder_name,
                req.founder_data,
                req.followup_qa,
                req.search_context,
            )
            grade = grade_output(analysis)
            try:
                score = int(grade.get("quality_score", 0))
            except (ValueError, TypeError):
                score = 0

            if score >= 3 and grade.get("feedback", "").strip():
                success = True
                break

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Analysis quality check failed after 3 attempts. Please try again."
            )

        # Attach metadata (same as original app.py)
        analysis["founder_profile"] = req.founder_data
        analysis["followup_qa"] = req.followup_qa
        analysis["original_idea"] = req.idea
        analysis["search_context"] = req.search_context

        # Save to SQLite and return the row ID so the frontend can PATCH tips later
        row_id = save_analysis(analysis)
        if row_id > 0:
            analysis["id"] = row_id

        return analysis

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Sub-pages: Readiness tips ─────────────────────────────────────────────────

@app.post("/api/readiness")
async def api_readiness(req: ReadinessRequest):
    """Generates MVP or Investment readiness tips."""
    if req.readiness_type not in ("mvp", "investment"):
        raise HTTPException(status_code=400, detail="readiness_type must be 'mvp' or 'investment'.")
    try:
        tips = None
        for _ in range(3):
            tips = generate_readiness_tips(
                req.analysis,
                req.readiness_type,
                req.search_context,
            )
            if tips.get("what_it_means") and tips.get("steps_to_become_ready"):
                break
        return tips
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Download: PPTX ────────────────────────────────────────────────────────────

@app.post("/api/ppt")
async def api_ppt(req: PptRequest):
    """Generates a PowerPoint pitch deck and streams it as a file download."""
    try:
        ppt_bytes: bytes = generate_ppt(req.analysis)
        return StreamingResponse(
            BytesIO(ppt_bytes),
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={"Content-Disposition": "attachment; filename=thynxai_pitch_deck.pptx"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Download: JSON report ─────────────────────────────────────────────────────

@app.post("/api/report/json")
async def api_report_json(req: ReportRequest):
    """Returns a JSON report file download."""
    try:
        content = save_json(req.analysis)
        return StreamingResponse(
            BytesIO(content.encode("utf-8")),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=analysis.json"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Download: Markdown report ─────────────────────────────────────────────────

@app.post("/api/report/md")
async def api_report_md(req: ReportRequest):
    """Returns a Markdown report file download."""
    try:
        content = save_markdown(req.analysis)
        return StreamingResponse(
            BytesIO(content.encode("utf-8")),
            media_type="text/markdown",
            headers={"Content-Disposition": "attachment; filename=report.md"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── History: List all saved analyses ─────────────────────────────────────────

@app.get("/api/analyses")
async def api_list_analyses():
    """Returns summary of all saved analyses (newest first)."""
    try:
        from database import get_all_analyses, DB_PATH
        import sqlite3 as _sq3
        conn = _sq3.connect(DB_PATH)
        conn.row_factory = _sq3.Row
        rows = conn.execute("SELECT id, founder_name, idea_summary, data, saved_at FROM analyses ORDER BY id DESC").fetchall()
        conn.close()
        import json as _j
        summaries = []
        for row in rows:
            try:
                d = _j.loads(row["data"])
                summaries.append({
                    "id": row["id"],
                    "founder_name": row["founder_name"] or "Unknown",
                    "idea_summary": (row["idea_summary"] or "")[:120],
                    "score": d.get("overall", {}).get("score", "?"),
                    "saved_at": row["saved_at"],
                })
            except Exception:
                pass
        return {"analyses": summaries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analyses/{analysis_id}")
async def api_get_analysis(analysis_id: int):
    """Returns full analysis JSON for a specific ID."""
    try:
        import sqlite3 as _sq3, json as _j
        from database import DB_PATH
        conn = _sq3.connect(DB_PATH)
        conn.row_factory = _sq3.Row
        row = conn.execute("SELECT id, data, saved_at FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
        conn.close()
        if not row:
            raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found.")
        result = _j.loads(row["data"])
        result["id"] = row["id"]
        result["_saved_at"] = row["saved_at"]
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class TipsUpdateRequest(BaseModel):
    tip_type: str   # "mvp" or "investment"
    tips: Dict[str, Any]

@app.patch("/api/analyses/{analysis_id}")
async def api_update_tips(analysis_id: int, req: TipsUpdateRequest):
    """Saves generated readiness tips into an existing analysis row."""
    if req.tip_type not in ("mvp", "investment"):
        raise HTTPException(status_code=400, detail="tip_type must be 'mvp' or 'investment'.")
    try:
        ok = update_analysis_tips(analysis_id, req.tip_type, req.tips)
        if not ok:
            raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found.")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/analyses/{analysis_id}")
async def api_delete_analysis(analysis_id: int):
    """Deletes a specific saved analysis."""
    try:
        import sqlite3 as _sq3
        from database import DB_PATH
        conn = _sq3.connect(DB_PATH)
        conn.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
        conn.commit()
        conn.close()
        return {"ok": True, "deleted_id": analysis_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Instant Chatbot ───────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []

@app.post("/api/chat")
async def api_chat(req: ChatRequest):
    """General-purpose chatbot backed by the offline AI model."""
    try:
        from analyzer import call_gemini, _parse_json_robust
        history_text = ""
        for msg in (req.history or [])[-6:]:
            role = "User" if msg.get("role") == "user" else "Assistant"
            history_text += f"{role}: {msg.get('content', '')}\n"

        prompt = f"""You are ThynxAI, a helpful AI assistant running fully offline.
You help startup founders. Be concise (under 150 words), friendly, and practical.

Previous conversation:
{history_text}User: {req.message}

Respond ONLY with this JSON: {{"reply": "your response here"}}"""

        raw = call_gemini(prompt, max_output_tokens=300)
        result = _parse_json_robust(raw, required_keys=["reply"])
        if result and result.get("reply"):
            return {"reply": result["reply"]}
        return {"reply": raw.strip()[:500] or "I am having trouble responding. Please try again."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Post-Analysis Follow-up Chat ──────────────────────────────────────────────

class FollowupRequest(BaseModel):
    analysis: Dict[str, Any]
    question: str
    history: Optional[List[Dict[str, str]]] = []

@app.post("/api/followup")
async def api_followup(req: FollowupRequest):
    """Answers follow-up questions about a specific analysis report."""
    try:
        from analyzer import call_gemini, _parse_json_robust
        a = req.analysis
        scores_text = ", ".join(
            f"{k.replace('_',' ')}: {v.get('score','?')}/10" if isinstance(v, dict) else f"{k}: {v}"
            for k, v in (a.get("scores") or {}).items()
        )
        history_text = ""
        for msg in (req.history or [])[-4:]:
            role = "User" if msg.get("role") == "user" else "Assistant"
            history_text += f"{role}: {msg.get('content', '')}\n"

        prompt = f"""You are ThynxAI, an AI startup mentor. Answer this founder's follow-up question about their report.

REPORT SUMMARY:
Founder: {a.get('founder_name','?')}
Idea: {a.get('idea_summary', a.get('original_idea','?'))}
Score: {a.get('overall', {}).get('score','?')}/10
Scores: {scores_text}
Verdict: {a.get('overall', {}).get('final_verdict','')}
MVP Ready: {a.get('overall', {}).get('is_mvp_ready','N/A')}
Investment Ready: {a.get('overall', {}).get('is_investment_ready','N/A')}

Previous Q&A:
{history_text}User question: {req.question}

Answer specifically based on this report. Be concise (under 200 words), honest, and encouraging.
Respond ONLY with this JSON: {{"reply": "your answer here"}}"""

        raw = call_gemini(prompt, max_output_tokens=400)
        result = _parse_json_robust(raw, required_keys=["reply"])
        if result and result.get("reply"):
            return {"reply": result["reply"]}
        return {"reply": raw.strip()[:600] or "Please rephrase your question and try again."}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
