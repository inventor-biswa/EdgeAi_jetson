"""
websearch.py — Offline mode for local deployment.

Original: Tavily real-time web search API
Replacement: Structured offline fallback that guides the local LLM
             to use its own training knowledge intelligently.

The fallback strings are carefully worded so the LLM understands:
  1. It is running offline — no live data is available
  2. It SHOULD still use its training knowledge to fill the gap
  3. It should clearly signal to the user when data is from training
     vs. live search

Optional: Set OFFLINE_MARKET_CACHE_FILE in .env to point to a
          pre-scraped JSON file of market data for specific domains.
          If the file exists, it will be used instead of the fallback.
"""

import os
import json
import datetime
from dotenv import load_dotenv

load_dotenv()

# ─── Optional: Pre-scraped cache file ────────────────────────────────────────
# If you run the app once with internet access and save Tavily results,
# point this env var to the saved JSON file for future offline use.
OFFLINE_CACHE_FILE = os.environ.get("OFFLINE_MARKET_CACHE_FILE", "")

_OFFLINE_YEAR = datetime.datetime.now().year


# ─── Cache loader ─────────────────────────────────────────────────────────────

def _load_cache(idea: str) -> dict | None:
    """
    Loads pre-scraped market data from a local JSON cache file if it exists.
    Cache format: {"competitors": "...", "market_size": "...", "recent_news": "..."}
    """
    if OFFLINE_CACHE_FILE and os.path.isfile(OFFLINE_CACHE_FILE):
        try:
            with open(OFFLINE_CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
            print(f"📂 Loaded offline market cache from: {OFFLINE_CACHE_FILE}")
            return cache
        except Exception as e:
            print(f"⚠️  Cache load failed: {e} — using fallback")
    return None


# ─── Offline fallback builder ─────────────────────────────────────────────────

def _build_offline_context(idea: str, location: str = "India") -> dict:
    """
    Returns structured offline fallback strings.
    These are NOT empty — they explicitly instruct the LLM to use
    training knowledge, and include the idea + location as context
    so the model can generate relevant domain-specific information.
    """
    idea_snippet = idea[:200].strip()

    competitors_prompt = (
        f"OFFLINE MODE (No live internet search available). "
        f"Based on your training knowledge up to {_OFFLINE_YEAR}, identify "
        f"the top 3-5 real startup competitors and established players in {location} "
        f"that are most relevant to this idea: '{idea_snippet}'. "
        f"Name actual companies, their market share if known, and what gap they leave open. "
        f"Clearly label this as training-knowledge data."
    )

    market_size_prompt = (
        f"OFFLINE MODE (No live internet search available). "
        f"Based on your training knowledge up to {_OFFLINE_YEAR}, estimate "
        f"the Total Addressable Market (TAM) size and CAGR growth rate in {location} "
        f"for the industry most relevant to: '{idea_snippet}'. "
        f"Provide specific numbers (crore / billion) if known from training data. "
        f"Clearly label this as training-knowledge estimate."
    )

    news_prompt = (
        f"OFFLINE MODE (No live internet search available). "
        f"Based on your training knowledge up to {_OFFLINE_YEAR}, describe "
        f"the most relevant industry trends, recent funding rounds, and regulatory "
        f"developments in {location} for the sector related to: '{idea_snippet}'. "
        f"Clearly label this as training-knowledge data."
    )

    return {
        "competitors": competitors_prompt,
        "market_size": market_size_prompt,
        "recent_news": news_prompt,
    }


# ─── Location extractor (unchanged from original) ────────────────────────────

def _extract_location(founder_data: dict) -> str:
    location = "India"
    if founder_data:
        raw = founder_data.get("location", "India")
        if "," in raw:
            location = raw.split(",")[-1].strip()
        else:
            location = raw
        if location == "Other":
            location = "Global"
    return location


# ─── Main entry point (same signature as original) ───────────────────────────

def get_search_context(idea: str, founder_data: dict = None) -> dict:
    """
    Offline replacement for the Tavily-based get_search_context().
    Keeps the exact same function signature so all callers work unchanged.

    Priority:
    1. Pre-scraped cache file (OFFLINE_MARKET_CACHE_FILE env var)
    2. Structured offline fallback strings (guides LLM to use training data)
    """
    location = _extract_location(founder_data)

    # Try loading from cache first
    cached = _load_cache(idea)
    if cached:
        return cached

    # Build offline fallback
    print(f"ℹ️  Offline mode — using training knowledge for market data ({location})")
    return _build_offline_context(idea, location)


# ─── Stub functions (kept for import compatibility) ───────────────────────────
# These match the original websearch.py interface in case any other module
# imports them directly.

def search_web(query: str) -> str:
    return (
        f"OFFLINE MODE: No live search. "
        f"Use training knowledge for query: {query[:150]}"
    )

def search_competitors(idea: str, location: str = "India") -> str:
    return _build_offline_context(idea, location)["competitors"]

def search_market_size(idea: str, location: str = "India") -> str:
    return _build_offline_context(idea, location)["market_size"]

def search_recent_news(idea: str, location: str = "India") -> str:
    return _build_offline_context(idea, location)["recent_news"]