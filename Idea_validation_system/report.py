"""
report.py — Generates output files from analysis.
Takes analysis dictionary → creates JSON and Markdown files.
No API calls happen here — just file writing.
"""

import json
import os
from datetime import datetime


# ─── File Saving Functions ───────────────────────────────────────────────────

def save_json(analysis: dict) -> str:
    json_string = json.dumps(analysis, indent=2)
    try:
        os.makedirs("outputs", exist_ok=True)
        with open("outputs/analysis.json", "w") as f:
            f.write(json_string)
    except Exception:
        pass
    return json_string


def save_markdown(analysis: dict) -> str:
    md_string = generate_markdown(analysis)
    try:
        os.makedirs("outputs", exist_ok=True)
        with open("outputs/report.md", "w", encoding="utf-8") as f:
            f.write(md_string)
    except Exception:
        pass
    return md_string

# ─── Markdown Generator ──────────────────────────────────────────────────────

def generate_markdown(analysis: dict) -> str:
    """
    Converts analysis dictionary into
    a human readable markdown string.
    """
    def safe(text):
        return str(text).replace("|", "-")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    scores = analysis.get("scores", {})
    overall = analysis.get("overall", {})
    profile = analysis.get("founder_profile", {})
    problem = analysis.get("problem_statement", {})
    solution = analysis.get("proposed_solution", {})
    innovation = analysis.get("core_innovation", {})
    market = analysis.get("market_landscape", {})
    failure = analysis.get("failure_analysis", {})
    support = analysis.get("support_required", {})
    tech = analysis.get("tech_stack", {})

    md = f"""# 🚀 Startup Idea Validation Report
Generated: {timestamp}
Founder: {analysis.get("founder_name", "N/A")}
Idea: {analysis.get("idea_summary", "N/A")}

---

## 👤 Founder Profile
- **Name:** {analysis.get("founder_name", "N/A")}
- **Age:** {profile.get("age", "N/A")}
- **Location:** {profile.get("location", "N/A")}
- **Background:** {profile.get("background", "N/A")}
- **Specific Field:** {profile.get("sub_field", "N/A")}
- **Role / Level:** {profile.get("role_level", "N/A")}
- **Skills:** {profile.get("skills", "N/A")}
- **Startup Experience:** {profile.get("startup_exp", "N/A")}
- **Talked to Users:** {profile.get("user_validation", "N/A")}
- **Industry Network:** {profile.get("industry_network", "N/A")}
- **Available Time:** {profile.get("available_time", "N/A")}
- **Main Goal:** {profile.get("main_goal", "N/A")}
- **Motivation:** {profile.get("motivation", "N/A")}
- **Already Tried:** {profile.get("already_tried", "N/A")}
- **Biggest Fear:** {profile.get("biggest_fear", "N/A")}
- **About Themselves:** {profile.get("about_self", "N/A")}

---

## 1️⃣ Problem Statement
- **Description:** {problem.get("description", "N/A")}
- **Target Audience:** {problem.get("target_audience", "N/A")}
- **Why Current Solutions Fail:** {problem.get("why_current_solutions_fail", "N/A")}
- **Real World Example:** {problem.get("real_world_example", "N/A")}
- **Who Suffers Most:** {problem.get("who_suffers_most", "N/A")}
- **Current Workarounds:** {problem.get("current_workarounds", "N/A")}
- **Market Size:** {problem.get("market_size_hint", "N/A")}
- **How Long Problem Exists:** {problem.get("how_long_problem_exists", "N/A")}

**Pain Points:**
{chr(10).join([f"- {point}" for point in problem.get("pain_points", [])])}

---

## 2️⃣ Proposed Solution
- **Simple Explanation:** {solution.get("simple_explanation", "N/A")}

**How It Works:**
{chr(10).join([f"- {step}" for step in solution.get("step_by_step_how_it_works", [])])}

**Key Features:**
{chr(10).join([f"- {feature}" for feature in solution.get("key_features", [])])}

- **Unfair Advantage:** {solution.get("unfair_advantage", "N/A")}
- **One Line Pitch:** {solution.get("one_line_pitch", "N/A")}

---

## 3️⃣ Core Innovation
- **Uniqueness:** {innovation.get("uniqueness", "N/A")}
- **Innovation Type:** {innovation.get("innovation_type", "N/A")}

---

## 4️⃣ Market Landscape
- **Similar Solutions:** {market.get("similar_solutions", "N/A")}
- **Competition Level:** {market.get("competition_level", "N/A")}
- **Market Gap:** {market.get("market_gap", "N/A")}

---

## 🔍 Market Intelligence (Offline Mode)
> This data is based on the AI model's training knowledge. Running fully offline — no live internet search.

**Competitors Found Online:**
{(analysis.get("search_context") or {}).get("competitors", "No data found")}

**Market Size Data:**
{(analysis.get("search_context") or {}).get("market_size", "No data found")}

**Recent News and Trends:**
{(analysis.get("search_context") or {}).get("recent_news", "No data found")}

---

## 5️⃣ Scores (1-10)
| Category | Score | Reasoning |
|----------|-------|-----------|
| Market Feasibility | {scores.get("market_feasibility", {}).get("score", "N/A")}/10 | {safe(scores.get("market_feasibility", {}).get("reasoning", "N/A"))} |
| Marketing Potential | {scores.get("marketing_potential", {}).get("score", "N/A")}/10 | {safe(scores.get("marketing_potential", {}).get("reasoning", "N/A"))} |
| Scalability | {scores.get("scalability", {}).get("score", "N/A")}/10 | {safe(scores.get("scalability", {}).get("reasoning", "N/A"))} |
| Revenue Potential | {scores.get("revenue_potential", {}).get("score", "N/A")}/10 | {safe(scores.get("revenue_potential", {}).get("reasoning", "N/A"))} |
| Technical Complexity | {scores.get("technical_complexity", {}).get("score", "N/A")}/10 | {safe(scores.get("technical_complexity", {}).get("reasoning", "N/A"))} |
| Execution Risk | {scores.get("execution_risk", {}).get("score", "N/A")}/10 | {safe(scores.get("execution_risk", {}).get("reasoning", "N/A"))} |

---

## ⚠️ How This Can Fail — Know Before You Build

### Why Similar Ideas Have Failed
{failure.get("why_similar_ideas_failed", "N/A")}

### Top 3 Things That Could Kill This Idea
{chr(10).join([f"{i+1}. {risk}" for i, risk in enumerate(failure.get("top_3_kill_risks", []))])}

### Hardest Obstacle in the First 90 Days
{failure.get("hardest_obstacle_first_90_days", "N/A")}

---

## 6️⃣ Support Required
- **Team Needed:** {support.get("team_needed", "N/A")}
- **Funding Stage:** {support.get("funding_stage", "N/A")}
- **Partnerships:** {support.get("partnerships", "N/A")}
- **Regulatory:** {support.get("regulatory", "N/A")}

---

## 7️⃣ Tech Stack
- **Backend:** {tech.get("backend", "N/A")}
- **Frontend:** {tech.get("frontend", "N/A")}
- **Database:** {tech.get("database", "N/A")}
- **Cloud:** {tech.get("cloud", "N/A")}
- **AI Tools:** {tech.get("ai_tools", "N/A")}

---

## 8️⃣ Overall Verdict
- **Overall Score:** {overall.get("score", "N/A")}/10
- **MVP Ready:** {overall.get("is_mvp_ready", "N/A")}
- **Investment Ready:** {overall.get("is_investment_ready", "N/A")}
- **Incubator Ready:** {overall.get("is_incubator_ready", "N/A")}

### Final Verdict
{overall.get("final_verdict", "N/A")}

---
*Report generated by ThynxAI Idea Lab*
"""
    return md