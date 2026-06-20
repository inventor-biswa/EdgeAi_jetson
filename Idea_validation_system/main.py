"""
main.py — CLI entry point.
Connects all files together.
Run this file to start the application.
"""

import sys
from analyzer import (
    validate_input,
    generate_followup_questions,
    analyze_idea,
    grade_output
)
from report import save_json, save_markdown


# ─── Main Function ────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("🚀 Welcome to ThynxAI Idea Lab — Startup Idea Validator")
    print("=" * 60)
    print()

    # ─── Step 1: Idea Submission ──────────────────────────────────────────
    print("📝 STEP 1: Tell us about your startup idea")
    print("-" * 60)

    idea = input("Please describe your startup idea in detail:\n> ")
    print()

    # ─── Validate Input ───────────────────────────────────────────────────
    print("⏳ Validating your idea...")

    validation = validate_input(idea)

    if validation["status"] == "INVALID":
        print(f"\n❌ Invalid Input: {validation['reason']}")
        print("Please restart and enter a valid startup idea.")
        sys.exit()

    print("✅ Idea accepted! Moving forward...\n")

    # ─── Step 2: Founder Information ──────────────────────────────────────
    print("👤 STEP 2: Tell us about yourself")
    print("-" * 60)

    founder_name = input("What is your name?\n> ")
    print()

    print("What is your background?")
    print("1. Technical")
    print("2. Non-Technical")
    print("3. Other")

    background_choice = input("\nEnter your choice (1/2/3):\n> ")
    print()

    if background_choice == "1":
        background = "Technical"
    elif background_choice == "2":
        background = "Non-Technical"
    elif background_choice == "3":
        background = "Other"
    else:
        print("❌ Invalid choice! Please restart and enter 1, 2 or 3.")
        sys.exit()

    print(f"✅ Got it {founder_name}! Background: {background}\n")

    # ─── Step 3: Follow-up Questions ──────────────────────────────────────
    print("❓ STEP 3: Follow-up Questions")
    print("-" * 60)
    print("⏳ Generating questions based on your idea...")
    print()

    questions = generate_followup_questions(idea, founder_name, background)

    followup_qa = []

    for i, question in enumerate(questions):
        print(f"Q{i+1}: {question}")
        answer = input("Your Answer:\n> ")
        print()
        followup_qa.append({
            "question": question,
            "answer": answer
        })

    print("✅ All questions answered! Moving forward...\n")

    # ─── Step 4: Analysis ─────────────────────────────────────────────────
    print("🧠 STEP 4: Analyzing your startup idea...")
    print("-" * 60)
    print("⏳ This may take a few seconds...\n")

    MAX_RETRIES = 3
    attempt = 0
    success = False
    analysis = None
    grade = None

    while attempt < MAX_RETRIES:
        print(f"⏳ Analyzing... (Attempt {attempt + 1}/{MAX_RETRIES})")
        analysis = analyze_idea(idea, founder_name, background, followup_qa)
        grade = grade_output(analysis)

        if grade["quality_score"] >= 3 and grade.get("feedback", "").strip():
            success = True
            break

        attempt += 1
        print(f"⚠️ Quality low ({grade['quality_score']}/5) — retrying...\n")

    if not success:
        print("❌ Analysis failed after 3 attempts.")
        print("👋 Please restart the program and try again.")
        sys.exit()

    print(f"✅ Analysis quality: {grade['quality_score']}/5")
    print(f"📊 Feedback: {grade['feedback']}\n")

    # ─── Save Reports ──────────────────────────────────────────────────────
    print("💾 Saving reports...")

    json_path = save_json(analysis)
    md_path = save_markdown(analysis)

    print(f"✅ JSON saved: {json_path}")
    print(f"✅ Report saved: {md_path}\n")

    # ─── Show Summary ──────────────────────────────────────────────────────
    print("=" * 60)
    print("🎉 ANALYSIS COMPLETE!")
    print("=" * 60)
    print(f"👤 Founder: {analysis['founder_name']}")
    print(f"💡 Idea: {analysis['idea_summary']}")
    print(f"⭐ Overall Score: {analysis['overall']['score']}/10")
    print(f"🚀 MVP Ready: {analysis['overall']['is_mvp_ready']}")
    print(f"💰 Investment Ready: {analysis['overall']['is_investment_ready']}")
    print(f"🏢 Incubator Ready: {analysis['overall']['is_incubator_ready']}")
    print("=" * 60)
    print(f"\n📄 Full report saved at: {md_path}")
    print(f"📦 JSON data saved at: {json_path}")


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()
