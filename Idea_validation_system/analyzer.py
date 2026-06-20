"""
analyzer.py — Core LLM logic (Jetson Offline Edition).

Replaces Google Gemini API with the Nemotron-3-Nano-4B model
running locally on Jetson Orin Nano via llama-server (llama.cpp).

API endpoint: http://127.0.0.1:8080/v1/chat/completions
This is OpenAI-compatible — same pattern as jetragv1/query.py.

MITIGATION LAYERS for 4B model JSON reliability:
  1. System prompt forces strict JSON-only output
  2. clean_json() strips markdown code fences
  3. extract_json_block() regex-extracts first {...} block
  4. repair_json() fixes trailing commas and control chars
  5. partial_parse_fallback() salvages truncated responses
  6. scaffold_missing_keys() fills any missing top-level keys
  7. Per-function retry with exponential back-off
"""

import os
import re
import json
import time
import requests
from dotenv import load_dotenv
from prompts import (
    get_analysis_prompt,
    get_validate_input_prompt,
    get_grade_output_prompt,
    get_adaptive_question_prompt,
    get_readiness_tips_prompt,
    get_pitch_deck_prompt,
)
from websearch import get_search_context

load_dotenv()

# ─── LLM Server Config ────────────────────────────────────────────────────────

LLM_API_URL = os.environ.get(
    "LLM_API_URL", "http://127.0.0.1:8080/v1/chat/completions"
)
LLM_MODEL = os.environ.get("LLM_MODEL", "my_model")

# System prompt injected into every call to enforce JSON-only output.
# This is the primary mitigation for the 4B model's tendency to add
# explanatory text around JSON.
_JSON_SYSTEM_PROMPT = (
    "You are a JSON-only AI assistant. "
    "You MUST respond with valid, complete JSON only. "
    "Do NOT include any explanation, markdown, or text outside the JSON. "
    "Do NOT wrap JSON in code fences or backticks. "
    "Do NOT add comments inside JSON. "
    "Output ONLY the raw JSON object."
)


# ─── Layer 1: Core HTTP call ──────────────────────────────────────────────────

def call_gemini(prompt: str, max_output_tokens: int = 2048) -> str:
    """
    Drop-in replacement for the original call_gemini().
    Keeps the same function signature so ALL other files work unchanged.

    Sends the prompt to Nemotron-3-Nano-4B on Jetson via llama-server.
    Includes connection-error handling with a user-friendly message.
    """
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": _JSON_SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        "max_tokens": max_output_tokens,
        "temperature": 0.0,   # deterministic for JSON reliability
        "stream": False,
    }

    try:
        response = requests.post(LLM_API_URL, json=payload, timeout=300)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    except requests.exceptions.ConnectionError:
        raise Exception(
            "❌ Cannot reach LLM server at "
            f"{LLM_API_URL}\n"
            "Make sure start_llm.sh has been run on the Jetson!"
        )
    except requests.exceptions.Timeout:
        raise Exception(
            "⏱️ LLM request timed out after 300 seconds. "
            "The model may be processing a very large prompt — try again."
        )
    except Exception as e:
        raise Exception(f"LLM API call failed: {str(e)}")


# ─── Layer 2: Markdown fence stripper ────────────────────────────────────────

def clean_json(raw: str) -> str:
    """
    Strips markdown code fences that 4B models sometimes add despite instructions.
    Handles variations: ```json, ```JSON, ```, and plain 'json' prefix.
    """
    raw = raw.strip()

    # Remove opening fence variants
    if raw.startswith("```"):
        parts = raw.split("```")
        # parts[1] contains the content between first pair of fences
        raw = parts[1] if len(parts) > 1 else raw
        if raw.lower().lstrip().startswith("json"):
            raw = raw.lstrip()[4:]

    # Catch bare 'json' prefix without fences
    if raw.lower().lstrip().startswith("json"):
        raw = raw.lstrip()[4:]

    return raw.strip()


# ─── Layer 3: Regex JSON extractor ────────────────────────────────────────────

def extract_json_block(text: str) -> str:
    """
    Finds and extracts the first complete {...} JSON object from text.
    Handles cases where the model outputs text before or after the JSON.
    Uses brace-counting to find the correct closing brace.
    """
    start = text.find("{")
    if start == -1:
        return text  # no JSON found, return as-is for downstream error

    depth = 0
    in_string = False
    escape_next = False

    for i, ch in enumerate(text[start:], start=start):
        if escape_next:
            escape_next = False
            continue
        if ch == "\\" and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]

    # Brace not closed — return from start to end (truncated output)
    return text[start:]


# ─── Layer 4: JSON repair ─────────────────────────────────────────────────────

def repair_json(text: str) -> str:
    """
    Fixes common JSON formatting errors from 4B models:
    - Trailing commas before ] or }
    - Non-printable control characters
    - Single quotes instead of double quotes (best-effort)
    """
    # Remove trailing commas
    text = re.sub(r",\s*([\]}])", r"\1", text)

    # Insert missing commas between properties: e.g. "value" "key":
    text = re.sub(r'([}\]"])\s+("[a-zA-Z0-9_]+"\s*:)', r'\1,\n\2', text)
    text = re.sub(r'(\d|true|false|null)\s+("[a-zA-Z0-9_]+"\s*:)', r'\1,\n\2', text)

    # Remove non-printable control characters (except \n \t)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    return text


# ─── Layer 5: Partial parse fallback ─────────────────────────────────────────

def partial_parse_fallback(text: str, required_keys: list) -> dict | None:
    """
    Handles truncated JSON from the model hitting the token limit.
    Tries to close the JSON by appending closing braces and reparsing.
    Returns a partial dict if successful, None if not salvageable.
    """
    # Try adding up to 3 levels of closing braces
    for closing in ["}", "}}", "}}}", "}}}}"]:
        candidate = text.rstrip().rstrip(",") + closing
        candidate = repair_json(candidate)
        try:
            result = json.loads(candidate)
            # Return if at least some required keys are present
            if any(k in result for k in required_keys):
                print(f"⚠️  Partial JSON recovered with {closing} — some fields may be missing")
                return result
        except json.JSONDecodeError:
            continue
    return None


# ─── Layer 6: Schema scaffold filler ─────────────────────────────────────────

def scaffold_missing_keys(result: dict, schema: dict) -> dict:
    """
    Fills in any missing top-level keys with safe defaults.
    This prevents KeyError crashes downstream when the model omits a section.
    """
    for key, default in schema.items():
        if key not in result:
            result[key] = default
            print(f"⚠️  Missing key '{key}' filled with default")
    return result


# ─── Master JSON parser (all 6 layers combined) ──────────────────────────────

def _parse_json_robust(
    raw_response: str,
    required_keys: list = None,
    schema: dict = None,
) -> dict | None:
    """
    Attempts JSON parsing through all mitigation layers in sequence.
    Returns parsed dict on success, None on total failure.
    """
    required_keys = required_keys or []

    # Layer 2 — strip markdown
    text = clean_json(raw_response)

    # Layer 3 — extract first {...} block
    text = extract_json_block(text)

    # Layer 4 — repair
    text = repair_json(text)

    # Layer 1 attempt — standard parse
    try:
        result = json.loads(text)
        if schema:
            result = scaffold_missing_keys(result, schema)
        return result
    except json.JSONDecodeError as e:
        print(f"⚠️  Standard JSON parse failed: {e}")

    # Layer 5 — partial parse on truncated output
    recovered = partial_parse_fallback(text, required_keys)
    if recovered:
        if schema:
            recovered = scaffold_missing_keys(recovered, schema)
        return recovered

    # All layers failed
    print("❌ All JSON repair layers failed.")
    print(f"   Raw snippet (first 300 chars): {raw_response[:300]}")
    return None


# ─── Analysis Schema (used by scaffold_missing_keys) ─────────────────────────

_ANALYSIS_SCHEMA = {
    "founder_name": "Unknown",
    "idea_summary": "No summary generated",
    "problem_statement": {
        "description": "N/A", "target_audience": "N/A",
        "why_current_solutions_fail": "N/A", "real_world_example": "N/A",
        "pain_points": [], "who_suffers_most": "N/A",
        "current_workarounds": "N/A", "market_size_hint": "N/A",
        "how_long_problem_exists": "N/A",
    },
    "proposed_solution": {
        "simple_explanation": "N/A", "step_by_step_how_it_works": [],
        "key_features": [], "unfair_advantage": "N/A", "one_line_pitch": "N/A",
    },
    "core_innovation": {"uniqueness": "N/A", "innovation_type": "N/A"},
    "market_landscape": {
        "similar_solutions": "N/A", "competition_level": "Medium", "market_gap": "N/A",
    },
    "scores": {
        "market_feasibility":  {"score": "5", "reasoning": "Analysis incomplete"},
        "marketing_potential": {"score": "5", "reasoning": "Analysis incomplete"},
        "scalability":         {"score": "5", "reasoning": "Analysis incomplete"},
        "revenue_potential":   {"score": "5", "reasoning": "Analysis incomplete"},
        "technical_complexity":{"score": "5", "reasoning": "Analysis incomplete"},
        "execution_risk":      {"score": "5", "reasoning": "Analysis incomplete"},
    },
    "support_required": {
        "team_needed": "N/A", "funding_stage": "Bootstrapped",
        "partnerships": "N/A", "regulatory": "N/A",
    },
    "tech_stack": {
        "backend": "N/A", "frontend": "N/A", "database": "N/A",
        "cloud": "N/A", "ai_tools": "N/A",
    },
    "overall": {
        "score": "5",
        "is_mvp_ready": "No — analysis could not complete fully",
        "is_investment_ready": "No — analysis could not complete fully",
        "is_incubator_ready": "No — analysis could not complete fully",
        "final_verdict": "The analysis ran in offline mode. Please retry for a full result.",
    },
}


# ─── Public API Functions ─────────────────────────────────────────────────────

def validate_input(idea: str) -> dict:
    """Validates whether the input is a real startup idea."""
    prompt = get_validate_input_prompt(idea)

    for attempt in range(3):
        try:
            raw = call_gemini(prompt, max_output_tokens=512)
            result = _parse_json_robust(raw, required_keys=["status"])
            if result and "status" in result:
                return result
        except Exception as e:
            print(f"⚠️  validate_input attempt {attempt+1} failed: {e}")
            time.sleep(1)

    return {"status": "VALID", "reason": "Validation inconclusive — proceeding anyway"}


# In-process cache: stores all 4 questions once generated for a session
_question_cache: dict = {}


def generate_single_question(
    idea: str,
    founder_name: str,
    founder_data: dict,
    history: list,
    search_context: dict = None,
) -> str:
    """
    On first call, generates ALL 4 questions at once and caches them.
    Subsequent calls return from the cache. Eliminates repeated questions.
    """
    from prompts import get_bulk_questions_prompt

    idx = len(history)  # 0, 1, 2, or 3
    cache_key = idea[:80]

    # Return cached question if available
    if cache_key in _question_cache and idx < len(_question_cache[cache_key]):
        print(f"Returning cached question {idx+1}")
        return _question_cache[cache_key][idx]

    # Generate all 4 at once on first call
    if idx == 0 or cache_key not in _question_cache:
        bulk_prompt = get_bulk_questions_prompt(idea, founder_name, founder_data, search_context)
        for attempt in range(3):
            try:
                raw = call_gemini(bulk_prompt, max_output_tokens=512)
                result = _parse_json_robust(raw, required_keys=["questions"])
                if result and isinstance(result.get("questions"), list) and len(result["questions"]) >= 4:
                    _question_cache[cache_key] = result["questions"][:4]
                    print(f"Cached all 4 questions in one shot")
                    return _question_cache[cache_key][0]
            except Exception as e:
                print(f"bulk question attempt {attempt+1} failed: {e}")
                time.sleep(1)

    # Fallback: single question with history context
    prompt = get_adaptive_question_prompt(
        idea, founder_name, founder_data, history, search_context
    )
    for attempt in range(3):
        try:
            raw = call_gemini(prompt, max_output_tokens=256)
            result = _parse_json_robust(raw, required_keys=["question"])
            if result and result.get("question"):
                return result["question"]
        except Exception as e:
            print(f"generate_single_question attempt {attempt+1} failed: {e}")
            time.sleep(1)

    fallbacks = [
        "Who would be your very first paying customer, and why would they pay?",
        "How do you plan to make money — subscriptions, one-time sale, or something else?",
        "What is the one thing your solution does that no existing tool does today?",
        "If you had to launch in 30 days with your current skills, what would you build first?",
    ]
    return fallbacks[min(idx, 3)]


def analyze_idea(
    idea: str,
    founder_name: str,
    founder_data: dict,
    followup_qa: list,
    search_context: dict = None,
) -> dict:
    """
    Core analysis — generates the 8-dimension startup report.
    Uses reduced token count (4096) to stay within Nemotron's context window
    while the multi-layer JSON repair ensures maximum completeness.
    """
    if search_context is None:
        search_context = get_search_context(idea, founder_data)

    prompt = get_analysis_prompt(
        idea, founder_name, founder_data, followup_qa, search_context
    )

    # 4096 tokens — balances completeness vs context window limit on 8GB Jetson
    for attempt in range(3):
        try:
            raw = call_gemini(prompt, max_output_tokens=4096)
            result = _parse_json_robust(
                raw,
                required_keys=["founder_name", "idea_summary", "overall"],
                schema=_ANALYSIS_SCHEMA,
            )
            if result:
                return result
        except Exception as e:
            print(f"⚠️  analyze_idea attempt {attempt+1} failed: {e}")
            time.sleep(2)

    # Last resort — return scaffolded defaults so app doesn't crash
    print("❌ Analysis failed after 3 attempts — returning scaffold")
    scaffold = _ANALYSIS_SCHEMA.copy()
    scaffold["founder_name"] = founder_name
    scaffold["idea_summary"] = idea[:120]
    return scaffold


def grade_output(analysis: dict) -> dict:
    """Grades the quality of the generated analysis (1-5 scale)."""
    prompt = get_grade_output_prompt(analysis)

    for attempt in range(3):
        try:
            raw = call_gemini(prompt, max_output_tokens=256)
            result = _parse_json_robust(raw, required_keys=["quality_score"])
            if result and "quality_score" in result:
                # Normalise — model may return int or string
                try:
                    result["quality_score"] = int(str(result["quality_score"]).strip())
                except (ValueError, TypeError):
                    result["quality_score"] = 3
                return result
        except Exception as e:
            print(f"⚠️  grade_output attempt {attempt+1} failed: {e}")
            time.sleep(1)

    # Mild default so retry loop in app.py doesn't loop forever
    return {"quality_score": 3, "feedback": "Grading inconclusive — proceeding"}


def generate_readiness_tips(
    analysis: dict, readiness_type: str, search_context: dict = None
) -> dict:
    """Generates MVP or investment readiness tips."""
    prompt = get_readiness_tips_prompt(analysis, readiness_type, search_context)

    _fallback = {
        "what_it_means": "Could not generate tips in offline mode. Please retry.",
        "why_not_ready": ["Analysis ran offline — limited market data available"],
        "steps_to_become_ready": ["Retry when the LLM server has more resources"],
        "realistic_timeline": "N/A",
        "first_action": "Restart the LLM server and try again",
        "what_investors_look_for": [],
    }

    for attempt in range(3):
        try:
            raw = call_gemini(prompt, max_output_tokens=2048)
            result = _parse_json_robust(raw, required_keys=["what_it_means"])
            if result:
                return result
        except Exception as e:
            print(f"⚠️  generate_readiness_tips attempt {attempt+1} failed: {e}")
            time.sleep(1)

    return _fallback


def generate_pitch_slides(analysis: dict) -> dict:
    """Generates pitch deck slide content."""
    prompt = get_pitch_deck_prompt(analysis)

    for attempt in range(3):
        try:
            raw = call_gemini(prompt, max_output_tokens=2048)

            # Pitch deck uses a slightly different extraction (top-level object)
            text = clean_json(raw)
            text = extract_json_block(text)
            text = repair_json(text)

            try:
                result = json.loads(text)
                print(f"✅ PPT generated on attempt {attempt+1}")
                return result
            except json.JSONDecodeError as e:
                recovered = partial_parse_fallback(text, ["slides", "title"])
                if recovered:
                    return recovered
                print(f"⚠️  PPT JSON parse failed (attempt {attempt+1}): {e}")

        except Exception as e:
            print(f"⚠️  generate_pitch_slides attempt {attempt+1} failed: {e}")
            time.sleep(1)

    print("❌ PPT generation failed after 3 attempts.")
    return {}