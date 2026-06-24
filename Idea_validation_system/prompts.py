"""
prompts.py — All AI prompts are stored here.
Each function builds one specific prompt.
No API calls happen here — just text building.
"""

import json

def get_adaptive_question_prompt(idea: str, founder_name: str, founder_data: dict, history: list, search_context: dict = None) -> str:
    """
    Compact prompt — generates ONE question at a time.
    Now explicitly lists already-asked questions to prevent repeats.
    """
    fd = founder_data
    already_asked = [item["question"] for item in history] if history else []
    already_asked_text = "\n".join(f"- {q}" for q in already_asked) if already_asked else "None yet"

    last_answer = history[-1]["answer"] if history else "No answer yet"
    question_num = len(history) + 1

    market_hint = ""
    if search_context:
        market_hint = f"MARKET CONTEXT: {str(search_context.get('competitors',''))[:200]}"

    return f"""You are a startup mentor interviewing a founder. Ask question {question_num} of 3.

IDEA: {idea}
FOUNDER: Name={founder_name}, Background={fd.get('background','?')}, Skills={fd.get('skills','?')}, Goal={fd.get('main_goal','?')}
{market_hint}

QUESTIONS ALREADY ASKED (DO NOT REPEAT OR REPHRASE THESE):
{already_asked_text}

LAST ANSWER FROM FOUNDER: {last_answer}

Rules:
- Ask about a completely DIFFERENT aspect than the questions above
- Ask one clear, open-ended question that invites a detailed answer — do NOT tell the founder to keep it short
- Make it specific to their idea, not generic
- Cover different themes across the 3 questions: customers, revenue, competition
- Question {question_num} should focus on: {"customers — who specifically will pay and why they would choose this over what they do today" if question_num == 1 else "revenue model — how exactly will this make money and what the pricing looks like" if question_num == 2 else "competitive edge — what makes this genuinely different from existing alternatives"}

Respond ONLY with this JSON:
{{"question": "your single question here?"}}"""


def get_bulk_questions_prompt(idea: str, founder_name: str, founder_data: dict, search_context: dict = None) -> str:
    """Generates all 3 AI questions at once to guarantee no repetition."""
    fd = founder_data
    market_hint = ""
    if search_context:
        market_hint = f"MARKET: {str(search_context.get('competitors',''))[:300]}"

    return f"""You are a startup mentor. Generate exactly 3 different interview questions for this founder.

IDEA: {idea}
FOUNDER: Name={founder_name}, Background={fd.get('background','?')}, Skills={fd.get('skills','?')}, Goal={fd.get('main_goal','?')}
{market_hint}

Rules:
- All 3 questions must be about DIFFERENT topics
- Q1: about their target customers (who specifically will pay and why they would choose this over existing alternatives)
- Q2: about their revenue model (how exactly they make money and what the pricing looks like)
- Q3: about their competitive edge (what makes this genuinely different from existing solutions)
- Each question must be open-ended and invite a detailed, thoughtful answer — do NOT tell the founder to keep it short
- Questions must be specific to this idea — no generic questions

Respond ONLY with this JSON:
{{"questions": ["question 1?", "question 2?", "question 3?"]}}"""


def get_analysis_prompt(idea: str, founder_name: str, founder_data: dict, followup_qa: list, search_context: dict = None) -> str:
    qa_text = "\n".join([
        f"Q: {item['question']}\nA: {item['answer']}"
        for item in followup_qa
    ])

    market_snippet = ""
    if search_context:
        market_snippet = (
            f"COMPETITORS: {str(search_context.get('competitors',''))[:300]}\n"
            f"MARKET SIZE: {str(search_context.get('market_size',''))[:200]}\n"
            f"TRENDS: {str(search_context.get('recent_news',''))[:200]}"
        )

    fd = founder_data
    founder_block = (
        f"Name: {founder_name}, Age: {fd.get('age','?')}, "
        f"Location: {fd.get('location','?')}, Background: {fd.get('background','?')}, "
        f"Skills: {fd.get('skills','?')}, Time: {fd.get('available_time','?')}, "
        f"Goal: {fd.get('main_goal','?')}, Startup exp: {fd.get('startup_exp','?')}"
    )

    return f"""You are a startup analyst. Analyse the idea and respond ONLY with valid JSON — no extra text outside JSON.

IDEA: {idea}
FOUNDER: {founder_block}

FOLLOW-UP Q&A:
{qa_text}

MARKET DATA:
{market_snippet if market_snippet else "Use your training knowledge for market data."}

STRICTNESS RULES — read before scoring:
- IMPORTANT: "proposed_solution" below always describes the founder's PLAN — what the product would do once built. Describing a plan is NOT evidence that it has been built. Never treat the existence of a detailed plan, feature list, or step-by-step flow as proof of a working MVP.
- "mvp_evidence" must be a direct quote taken ONLY from the FOLLOW-UP Q&A ANSWERS printed above — NOT from the FOUNDER background or skills section. Re-read each Q&A answer one by one and look for the founder saying any of these things in their own words: "I already have", "I built", "I have X paying customers", "working prototype", "I tested it with real users", "people are using it", "I launched". If you find such a phrase in a Q&A answer, copy it exactly as your mvp_evidence. The FOUNDER background/skills section (before the Q&A) does NOT count — prior work history is not evidence of this specific product being built. If no Q&A answer contains such a phrase — set "mvp_evidence" to the exact literal string "NONE".
- "is_mvp_ready" = "Yes" ONLY if "mvp_evidence" above is not "NONE". If "mvp_evidence" is "NONE", "is_mvp_ready" MUST be "No — no working prototype or user testing was described, only a plan for what will be built later".
- "is_investment_ready" and "is_incubator_ready" must be tied to the 6 dimension scores below: if the average of the 6 scores is below 6/10, OR execution_risk or revenue_potential is weak, the answer must be "No — <name the specific weak dimension>".
- Never default to an optimistic "Yes" to be encouraging. Founders are non-technical and are relying on this report to know where they really stand — an inflated verdict actively harms them. Honesty first, encouragement second.
- Every reasoning field must reference something specific from the founder's actual input or the market data — not a generic statement that could apply to any idea.

SCORING RUBRIC — calibrate each score honestly before writing it:
- 1-2: Critically flawed. No evidence at all, or strong evidence the idea will fail in this dimension.
- 3-4: Weak. Significant gaps with no plan to address them; below what investors or users would accept.
- 5: Average. Meets minimum bar but nothing stands out; many early-stage ideas land here.
- 6-7: Moderate to good. Real evidence of strength, but at least one clear gap still needs work.
- 8-9: Strong. Concrete, specific evidence of advantage; only minor gaps remain.
- 10: Exceptional. Reserved for ideas with proven traction, unique moat, or rare founder advantage.
IMPORTANT: most early-stage ideas with no product built yet score 3-5 across most dimensions. Scores of 7+ require specific, concrete evidence from the founder's input — not potential. If you find yourself writing 6 or 7 for every dimension, stop and re-evaluate each one individually against this rubric.
For execution_risk specifically: a founder with limited available time (weekends only, part-time), no technical skills in a tech-dependent idea, no co-founder, and no developer lined up must score 2-4. execution_risk of 5+ requires the founder to have at least one of: relevant technical skill, full-time availability, or an existing team member.

Output ONLY this exact JSON structure. Replace ALL placeholder text with real analysis. No null values allowed:
{{
  "founder_name": "{founder_name}",
  "idea_summary": "one sentence describing what this product does",
  "problem_statement": {{
    "description": "3-4 sentences describing the problem clearly and concretely, in plain language",
    "target_audience": "who specifically faces this problem",
    "why_current_solutions_fail": "2-3 sentences on why existing solutions are not enough",
    "real_world_example": "short story of a real person with this problem",
    "pain_points": ["specific pain 1", "specific pain 2", "specific pain 3"],
    "who_suffers_most": "the most affected group",
    "current_workarounds": "what people do today instead",
    "market_size_hint": "estimated market size with numbers",
    "how_long_problem_exists": "how long this problem has existed"
  }},
  "proposed_solution": {{
    "simple_explanation": "explain to a 10 year old in 3-4 sentences",
    "step_by_step_how_it_works": ["user does step 1", "step 2 happens", "step 3 result"],
    "key_features": ["feature 1 description", "feature 2 description", "feature 3 description"],
    "unfair_advantage": "unique edge this specific founder has",
    "one_line_pitch": "one sentence: what it does plus who it helps plus why it works"
  }},
  "core_innovation": {{
    "uniqueness": "what makes it genuinely unique",
    "innovation_type": "Technology or Business Model or Both"
  }},
  "market_landscape": {{
    "similar_solutions": "name real existing competitors",
    "competition_level": "Low or Medium or High",
    "market_gap": "specific gap this idea fills"
  }},
  "scores": {{
    "market_feasibility": {{"score": "<your honest 1-10 integer>", "reasoning": "EXACTLY 3-4 sentences: (1) cite specific evidence from the idea or Q&A that set this score, (2) explain what that evidence means for market success in plain language, (3) name the biggest gap or risk in this dimension for this idea, (4) one concrete next action to improve this score."}},
    "marketing_potential": {{"score": "<your honest 1-10 integer>", "reasoning": "EXACTLY 3-4 sentences: (1) cite specific evidence from the idea or Q&A that set this score, (2) explain what that evidence means for reaching customers in plain language, (3) name the biggest gap or risk in this dimension for this idea, (4) one concrete next action to improve this score."}},
    "scalability": {{"score": "<your honest 1-10 integer>", "reasoning": "EXACTLY 3-4 sentences: (1) cite specific evidence from the idea or Q&A that set this score, (2) explain what that evidence means for growth in plain language, (3) name the biggest gap or risk in this dimension for this idea, (4) one concrete next action to improve this score."}},
    "revenue_potential": {{"score": "<your honest 1-10 integer>", "reasoning": "EXACTLY 3-4 sentences: (1) cite specific evidence from the idea or Q&A that set this score, (2) explain what that evidence means for making money in plain language, (3) name the biggest gap or risk in this dimension for this idea, (4) one concrete next action to improve this score."}},
    "technical_complexity": {{"score": "<your honest 1-10 integer>", "reasoning": "EXACTLY 3-4 sentences: (1) cite specific evidence from the idea or Q&A and the founder's skills that set this score, (2) explain what that evidence means for building the product in plain language, (3) name the biggest technical gap or risk for this idea, (4) one concrete next action to improve this score."}},
    "execution_risk": {{"score": "<your honest 1-10 integer>", "reasoning": "EXACTLY 3-4 sentences: (1) cite specific evidence from the founder profile (especially available time and skills) and Q&A that set this score, (2) explain what that means for shipping in plain language, (3) name the biggest execution gap or risk, (4) one concrete next action to reduce this risk."}}
  }},
  "support_required": {{
    "team_needed": "what team roles are needed",
    "funding_stage": "Bootstrapped or Seed or VC",
    "partnerships": "key partnerships needed",
    "regulatory": "any regulatory requirements"
  }},
  "tech_stack": {{
    "backend": "recommended backend technology",
    "frontend": "recommended frontend technology",
    "database": "recommended database",
    "cloud": "cloud or local hosting recommendation",
    "ai_tools": "AI tools if needed or none"
  }},
  "failure_analysis": {{
    "why_similar_ideas_failed": "2-3 sentences naming REAL companies or well-known attempts in this space that failed, and the specific reason each one failed — not generic market conditions, but the actual cause (e.g. wrong unit economics, regulatory block, wrong customer segment, couldn't retain users). Use real names if you know them.",
    "top_3_kill_risks": [
      "Kill risk 1: the single most likely thing to kill THIS specific idea, with one sentence explaining why it is dangerous for this founder",
      "Kill risk 2: second most dangerous threat specific to this idea and founder's situation",
      "Kill risk 3: third risk this founder must prepare for before launch"
    ],
    "hardest_obstacle_first_90_days": "2-3 sentences describing the ONE hardest obstacle this specific founder will hit in the first 90 days — referencing their background, skills, and available time — and one concrete suggestion for how to get past it"
  }},
  "overall": {{
    "score": "<your honest 1-10 integer — average of the 6 scores above>",
    "mvp_evidence": "exact quote from IDEA or FOLLOW-UP Q&A proving something is already built/tested, or the literal string NONE",
    "is_mvp_ready": "Yes or No — must follow the STRICTNESS RULES above, name specific missing evidence if No",
    "is_investment_ready": "Yes or No — must follow the STRICTNESS RULES above, name the specific weak dimension if No",
    "is_incubator_ready": "Yes or No — must follow the STRICTNESS RULES above, name the specific weak dimension if No",
    "final_verdict": "4-6 honest sentences plainly stating what is missing and what to do next — encouraging in tone but never inflating the reality"
  }}
}}"""


def get_validate_input_prompt(idea: str) -> str:
    return f"""
<role>
You are a startup idea validator.
</role>

<input>
{idea}
</input>

<instructions>
Think carefully about whether this is a real startup idea.

Rubric:
- If random gibberish or keyboard smashing → INVALID
- If offensive or harmful content → INVALID
- If less than 10 meaningful words → INVALID
- If a real business concept → VALID

Do not use LaTeX or any math notation. Use plain text only.

After thinking, respond ONLY in this exact JSON format:
{{
  "status": "VALID or INVALID",
  "reason": "one line explanation"
}}
</instructions>
"""


def get_grade_output_prompt(analysis: dict) -> str:
    analysis_text = json.dumps(analysis, indent=2)

    return f"""
<role>
You are an expert evaluator of startup analyses.
</role>

<analysis>
{analysis_text}
</analysis>

<instructions>
Think carefully about the quality of this analysis.

Rubric:
- Does it have a clear problem statement?
- Does it have scores with reasoning?
- Does it have a tech stack suggestion?
- Is the overall verdict logical?

Do not use LaTeX or any math notation. Use plain text only.

After thinking, respond ONLY in this exact JSON format:
{{
  "quality_score": "<integer 1 to 5 only>",
  "feedback": "maximum 10 words only"
}}
</instructions>
"""


def get_readiness_tips_prompt(analysis: dict, readiness_type: str ,search_context: dict = None) -> str:
    
    founder_name = analysis.get("founder_name", "the founder")
    idea_summary = analysis.get("idea_summary", "not specified")
    overall = analysis.get("overall", {})
    scores = analysis.get("scores", {})
    problem = analysis.get("problem_statement", {})
    solution = analysis.get("proposed_solution", {})
    founder_profile = analysis.get("founder_profile", {})

    scores_text = "\n".join([
        f"- {k.replace('_', ' ').title()}: {v.get('score', 'N/A')}/10 — {v.get('reasoning', '')}"
        for k, v in scores.items()
    ])

    if search_context:
        market_block = f"""
<real_market_data>
This is REAL current data about this idea's market.
Use this to give specific, accurate, actionable tips.
NEVER use this data to discourage — use it to guide!
Even in a competitive market there is always a path forward!

COMPETITORS:
{search_context.get("competitors", "No data found")}

MARKET SIZE:
{search_context.get("market_size", "No data found")}

RECENT TRENDS:
{search_context.get("recent_news", "No data found")}
</real_market_data>
"""
    else:
        market_block = ""

    if readiness_type == "mvp":
        type_instruction = """
Your job is to tell this founder EXACTLY what they need to do to make their idea MVP ready.

MVP means — the smallest possible working version of the product that real users can actually use and give feedback on.

Generate tips that are:
- Specific to THIS idea — not generic advice
- Use REAL competitor names and market numbers from <real_market_data>
- Never say "research the market" — tell them WHAT the market shows
- Never say "talk to users" — tell them WHICH specific users and WHERE
- Never say "build a prototype" — tell them WHAT exactly to build first
- Give specific Indian platforms, tools, communities where relevant
- Simple enough for a school student to understand and act on
- Honest about what is missing right now
- Encouraging — every problem has a solution!

CRITICAL RULES:
- what_it_means → explain MVP using THIS idea as example with real numbers
- why_not_ready → use actual gaps found in search data, not generic reasons
- steps_to_become_ready → each step must be specific and actionable
  Bad step  → "Build your product"
  Good step → "Build a WhatsApp bot first — no app needed, zero cost,
               test with 10 kirana store owners in your city this week"
- realistic_timeline → based on founder's available time from profile
- first_action → one sentence, so specific they can do it tomorrow morning

Example of bad tips:
"Research your competitors and understand the market"
"Talk to potential users and get feedback"
"Build an MVP and test it"

Example of good tips:
"Blinkit holds 45% market share but has zero presence in
tier-3 cities — your MVP should target exactly these areas.
Start with one locality, 10 store owners, WhatsApp only."

Respond ONLY in this exact JSON format:
{
  "what_it_means": "explain what MVP means for THIS specific idea with a real example — 4-5 plain-language sentences, concrete and specific, not generic",
  "why_not_ready": ["specific reason 1 from real market data, 2-3 sentences with concrete evidence", "specific reason 2, 2-3 sentences", "specific reason 3, 2-3 sentences"],
  "steps_to_become_ready": ["very specific step 1", "very specific step 2", "very specific step 3 — add up to 5 if needed"],
  "realistic_timeline": "honest timeline based on founder available time — e.g. 4-6 weeks working part time",
  "first_action": "one ultra-specific thing they can do tomorrow morning — no vague advice"
}
"""
    else:
        type_instruction = """
Your job is to tell this founder EXACTLY what they need to do to make their idea investment ready.

Investment ready means — the idea is structured, validated and promising enough that an Indian investor, incubator or angel would consider putting money into it.

Generate tips that are:
- Specific to THIS idea — not generic advice
- Use REAL market numbers, competitor funding data from <real_market_data>
- Never say "show traction" — tell them WHAT traction looks like in numbers
- Never say "find investors" — tell them WHAT TYPE of investors suit this idea
  example: angel investors, government grants, state incubators, startup accelerators
- Never say "validate your idea" — tell them HOW with specific metrics
- Reference real Indian funding landscape where relevant
- Simple enough for a school student to understand and act on
- Honest about what is missing right now
- Encouraging — every problem has a solution!

CRITICAL RULES:
- what_it_means → explain investment readiness using THIS idea + real market context
- why_not_ready → use actual gaps from scores and real market data
  Bad  → "You don't have enough traction"
  Good → "Early stage investors in this space typically look for
          at least 1000 active users and ₹1L monthly revenue
          before writing a seed check — you are not there yet"
- steps_to_become_ready → ultra specific roadmap
  Bad  → "Build your product and get users"
  Good → "Look for government startup programs and incubators
          in your state — they offer free mentorship and 
          investor connections specifically for early stage ideas"
- what_investors_look_for → specific to THIS idea's industry
  Use real funding patterns from search data if available
  Example → "Quick commerce investors look for: dark store unit economics,
             order frequency per user per week, CAC vs LTV ratio"
- realistic_timeline → based on founder's available time and current score
- first_action → one sentence, ultra specific, doable tomorrow morning

Example of bad tips:
"Get more users and show growth"
"Approach investors with a good pitch deck"
"Validate your business model"

Example of good tips:
"Look for early stage accelerators that accept pre-revenue ideas —
many government and private programs offer free mentorship
and investor connections for ideas at exactly your stage."

Respond ONLY in this exact JSON format:
{
  "what_it_means": "explain investment readiness for THIS idea with real market context — 4-5 plain-language sentences, concrete and specific, not generic",
  "why_not_ready": ["specific reason 1 with real data, 2-3 sentences with concrete evidence", "specific reason 2, 2-3 sentences", "specific reason 3, 2-3 sentences"],
  "steps_to_become_ready": ["ultra specific step 1", "ultra specific step 2", "ultra specific step 3 — add up to 5 if needed"],
  "what_investors_look_for": ["specific metric or signal 1 for THIS industry", "specific thing 2", "specific thing 3", "specific thing 4"],
  "realistic_timeline": "honest timeline based on founder available time and current readiness",
  "first_action": "one ultra-specific thing they can do tomorrow morning — name the exact platform, person or action"
}
"""

    return f"""
<role>
You are a warm and honest startup mentor.
You genuinely want this founder to succeed.
You give specific, actionable, simple advice.
You never give fake praise — but always stay encouraging.
Do not use LaTeX or any math notation. Use plain text only.
</role>

<founder_info>
Name: {founder_name}
Background: {founder_profile.get("background", "not specified")}
Age: {founder_profile.get("age", "not specified")}
Location: {founder_profile.get("location", "not specified")}
Skills: {founder_profile.get("skills", "not specified")}
Available Time: {founder_profile.get("available_time", "not specified")}
Main Goal: {founder_profile.get("main_goal", "not specified")}
Already Tried: {founder_profile.get("already_tried", "not specified")}
</founder_info>

<idea_summary>
{idea_summary}
</idea_summary>

<current_scores>
{scores_text}
</current_scores>

<current_verdict>
MVP Ready: {overall.get("is_mvp_ready", "N/A")}
Investment Ready: {overall.get("is_investment_ready", "N/A")}
Incubator Ready: {overall.get("is_incubator_ready", "N/A")}
Final Verdict: {overall.get("final_verdict", "N/A")}
</current_verdict>

<problem_summary>
{problem.get("description", "N/A")}
</problem_summary>

<solution_summary>
{solution.get("simple_explanation", "N/A")}
</solution_summary>

{market_block}

<instructions>
{type_instruction}
</instructions>
"""


def get_pitch_deck_prompt(analysis: dict) -> str:

    relevant = {
        "founder_name": analysis.get("founder_name"),
        "idea_summary": analysis.get("idea_summary"),
        "problem_statement": analysis.get("problem_statement", {}),
        "proposed_solution": analysis.get("proposed_solution", {}),
        "core_innovation": analysis.get("core_innovation", {}),
        "market_landscape": analysis.get("market_landscape", {}),
        "scores": analysis.get("scores", {}),
        "tech_stack": analysis.get("tech_stack", {}),
        "support_required": analysis.get("support_required", {}),
        "overall": analysis.get("overall", {}),
        "founder_profile": analysis.get("founder_profile", {}),
        "search_context": analysis.get("search_context", "")
    }

    return f"""
<role>
You are a startup pitch deck expert preparing investor-ready slide content.
</role>

<analysis>
{json.dumps(relevant, indent=2, ensure_ascii=True)}
</analysis>

<instructions>
Extract and generate content for each placeholder key below.
Use ONLY data from the analysis. Do not hallucinate.
Use real competitor names and market numbers from search_context where available.
Keep all values short and punchy — max 10 words per field unless specified.
No slashes, symbols, asterisks, or decorations in any value.

<json_safety_contract>
- ALL keys and values must use double quotes
- No trailing commas
- No special characters or symbols in values
- Every opened bracket must have a matching closing bracket
- Output must start with {{ and end with }}
- Must be valid JSON that passes json.loads()
</json_safety_contract>

Respond ONLY in this exact JSON format:
{{
  "idea_title": "short punchy name for the idea",
  "one_line_pitch": "one sentence — what it does and who it helps",
  "founder_name": "founder name",
  "founder_role": "founder role like CEO or Founder",
  "founder_email": "not available",
  "founder_phone": "not available",
  "founder_website": "not available",

  "idea_summary": "2 lines max — what the company does",
  "solution_explanation": "2 lines max — how the idea solves the problem",

  "trend_1": "trend title",
  "trend_1_detail": "one line detail",
  "trend_2": "trend title",
  "trend_2_detail": "one line detail",
  "trend_3": "trend title",
  "trend_3_detail": "one line detail",
  "trend_4": "trend title",
  "trend_4_detail": "one line detail",

  "stat_1_number": "a real market number",
  "stat_1_label": "what this number means",
  "stat_2_number": "another number",
  "stat_2_label": "what this number means",
  "stat_3_number": "another number",
  "stat_3_label": "what this number means",

  "market_size": "TAM number like 4.2B",
  "market_size_label": "what this market size represents",

  "competitor_1": "real competitor name",
  "comp_1_feature": "their key feature",
  "comp_1_value": "their value prop",
  "comp_1_price": "their pricing",
  "comp_1_trial": "Yes or No",
  "comp_1_level": "Low or High",
  "comp_1_share": "market share if known",

  "competitor_2": "real competitor name",
  "comp_2_feature": "their key feature",
  "comp_2_value": "their value prop",
  "comp_2_price": "their pricing",
  "comp_2_trial": "Yes or No",
  "comp_2_level": "Low or High",
  "comp_2_share": "market share if known",

  "competitor_3": "real competitor name",
  "comp_3_feature": "their key feature",
  "comp_3_value": "their value prop",
  "comp_3_price": "their pricing",
  "comp_3_trial": "Yes or No",
  "comp_3_level": "Low or High",
  "comp_3_share": "market share if known",

  "competitor_4": "real competitor name",
  "comp_4_feature": "their key feature",
  "comp_4_value": "their value prop",
  "comp_4_price": "their pricing",
  "comp_4_trial": "Yes or No",
  "comp_4_level": "Low or High",
  "comp_4_share": "market share if known",

  "competitor_5": "real competitor name",
  "comp_5_feature": "their key feature",
  "comp_5_value": "their value prop",
  "comp_5_price": "their pricing",
  "comp_5_trial": "Yes or No",
  "comp_5_level": "Low or High",
  "comp_5_share": "market share if known",

  "competitor_6": "real competitor name",
  "comp_6_feature": "their key feature",
  "comp_6_value": "their value prop",
  "comp_6_price": "their pricing",
  "comp_6_trial": "Yes or No",
  "comp_6_level": "Low or High",
  "comp_6_share": "market share if known",

  "competitor_7": "real competitor name",
  "comp_7_feature": "their key feature",
  "comp_7_value": "their value prop",
  "comp_7_price": "their pricing",
  "comp_7_trial": "Yes or No",
  "comp_7_level": "Low or High",
  "comp_7_share": "market share if known",

  "feature_1": "feature name",
  "feature_1_detail": "one line detail",
  "feature_2": "feature name",
  "feature_2_detail": "one line detail",
  "feature_3": "feature name",
  "feature_3_detail": "one line detail",
  "feature_4": "feature name",
  "feature_4_detail": "one line detail",
  "feature_5": "feature name",
  "feature_5_detail": "one line detail",
  "feature_6": "feature name",
  "feature_6_detail": "one line detail",

  "ask_1": "first ask point",
  "ask_2": "second ask point",
  "ask_3": "third ask point",
  "ask_4": "fourth ask point",
  "ask_5": "fifth ask point",
  "ask_6": "sixth ask point",
  "ask_7": "seventh ask point",
  "ask_8": "eighth ask point",

  "founder_role": "CEO or Founder",

  "tam": "total addressable market number",
  "tam_description": "one line what TAM means for this idea",
  "sam": "serviceable addressable market number",
  "sam_description": "one line what SAM means for this idea",
  "som": "serviceable obtainable market number",
  "som_description": "one line what SOM means for this idea"
}}
</instructions>
"""