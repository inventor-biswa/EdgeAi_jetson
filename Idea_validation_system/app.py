"""
app.py — Streamlit UI for ThynxAI Idea Lab
Run with: streamlit run app.py
"""

import streamlit as st
from analyzer import (
    validate_input,
    generate_single_question,
    analyze_idea,
    grade_output,
    generate_readiness_tips,
    generate_pitch_slides
)
from report import save_json, save_markdown
from database import save_analysis
from websearch import get_search_context
from ppt import generate_ppt




# ─── Page Config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="ThynxAI Idea Lab",
    page_icon="🚀",
    layout="centered"
)


# ─── Title ───────────────────────────────────────────────────────────────────

st.title("🚀 ThynxAI Idea Lab")
st.subheader("AI-Powered Startup Idea Validator")
st.divider()


# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("📌 About")
    st.write("This tool analyzes your startup idea using AI.")
    st.divider()
    st.write("**How it works:**")
    st.write("1. Describe your idea")
    st.write("2. Tell us about yourself")
    st.write("3. Answer follow-up questions")
    st.write("4. Get full analysis report")
    st.divider()
    st.write("🤖 Powered by Qwen2.5-7B-Instruct")
    st.write("⚡ Running offline on NVIDIA Jetson")


# ─── Session State ────────────────────────────────────────────────────────────
defaults = {
    "step": 1,
    "idea": "",
    "founder_name": "",
    "questions": [],
    "followup_qa": [],
    "analysis": None,
    "current_question_index": 0,
    "answers_history": [],
    "chat_index": 0,
    "chat_history": [],
    "founder_data": {},
    "sub_page": None,
    "search_context": None 
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ─── Step 1: Idea Input ───────────────────────────────────────────────────────

if st.session_state.step == 1:
    st.header("📝 Step 1: Describe Your Startup Idea")
    st.divider()

    idea = st.text_area(
        "Please describe your startup idea in detail:",
        height=150,
        placeholder="e.g. An AI app that helps restaurants reduce food waste..."
    )

    if st.button("Next →", key="btn_step1"):
        if not idea.strip():
            st.error("❌ Please enter your startup idea first!")
        else:
            with st.spinner("⏳ Validating your idea..."):
                validation = validate_input(idea)

            if validation["status"] == "INVALID":
                st.error(f"❌ {validation['reason']}")
            else:
                st.session_state.idea = idea
                st.session_state.step = 2
                st.rerun()


# ─── Step 2: Founder Information ─────────────────────────────────────────────

elif st.session_state.step == 2:
    st.header("👤 Step 2: Founder Information")
    st.divider()

# ─── Helper: Save and move forward ───────────────────────────────────────────
    def save_and_next(question: str, answer: str, key: str):
        st.session_state.chat_history.append({"question": question, "answer": answer})
        st.session_state.founder_data[key] = answer
        st.session_state[key] = answer
        st.session_state.chat_index += 1
        st.rerun()


    # ─── Helper: Go back ─────────────────────────────────────────────────────────
    def go_back():
        if st.session_state.chat_index > 0:
            st.session_state.chat_index -= 1
            if st.session_state.chat_history:
                st.session_state.chat_history.pop()
            if st.session_state.founder_data:
                last_key = list(st.session_state.founder_data.keys())[-1]
                del st.session_state.founder_data[last_key]
                if last_key in st.session_state:
                    del st.session_state[last_key]
            st.rerun()


    # ─── Helper: Skills question ─────────────────────────────────────────────────
    def _show_skills_question(bg):
        st.markdown("🤖 **What skills do you have? (Select all that apply)**")

        skills_map = {
            "Technical":     ["Python / Programming", "Web Development", "Mobile App Dev",
                              "Machine Learning / AI", "Cloud / DevOps", "Database / SQL",
                              "Cybersecurity", "UI / UX Design", "System Design", "GitHub / Open Source"],
            "Non-Technical": ["Communication / Speaking", "Teaching / Training", "Writing / Storytelling",
                              "Community Building", "Event Management", "Customer Handling",
                              "Field Research", "Photography / Video", "Social Media", "Language Skills"],
            "Business":      ["Sales / Cold Calling", "Digital Marketing", "Finance / Budgeting",
                              "Business Planning", "Negotiation", "Team Leadership",
                              "Networking", "Pitching", "E-commerce", "Legal Basics"],
            "Research":      ["Data Collection", "Statistical Analysis", "Academic Writing",
                              "Lab / Experimental Work", "Python / R", "Grant Writing",
                              "Patent Filing", "Public Speaking", "Teaching", "Policy Writing"],
            "Student":       ["Basic Coding", "MS Office / Google Docs", "Social Media",
                              "Research / Googling", "Public Speaking", "Event Organizing",
                              "Content Writing", "Basic Design (Canva)", "Video Editing", "Freelancing"],
            "Creative":      ["UI / UX (Figma)", "Graphic Design", "Video Editing",
                              "Photography", "Copywriting", "Social Media Growth",
                              "Branding", "Motion Graphics", "Music Production", "Freelance Work"],
            "Self Taught":   ["Self Taught Coding", "Self Taught Business Skills",
                              "Self Taught Design", "YouTube / Online Courses",
                              "Hands-on Project Experience", "Community / Network Building",
                              "Problem Solving", "Resourcefulness", "Learning Fast", "Street Smart"],
            "Just Idea":     ["Common Sense / Observation", "Communication", "Networking",
                              "Research / Reading", "Problem Spotting", "Convincing Others",
                              "Basic Computer Use", "Social Media", "Managing People", "Street Smart"],
            "Beginner":      ["Willingness to Learn", "Common Sense", "Communication",
                              "Hard Work / Dedication", "Social Media (basic)", "Basic Computer Use",
                              "Observation Skills", "Helping Others", "Street Smart",
                              "Nothing specific yet — and that is okay!"]
        }

        if "Non-Technical" in bg:     key = "Non-Technical"
        elif "Technical" in bg:       key = "Technical"
        elif "Business" in bg:        key = "Business"
        elif "Research" in bg:        key = "Research"
        elif "Student" in bg:         key = "Student"
        elif "Creative" in bg:        key = "Creative"
        elif "Self Taught" in bg:     key = "Self Taught"
        elif "Just Have" in bg:       key = "Just Idea"
        else:                         key = "Beginner"

        skill_list = skills_map.get(key, skills_map["Beginner"])
        selected = []
        cols = st.columns(2)
        for i, skill in enumerate(skill_list):
            with cols[i % 2]:
                if st.checkbox(skill, key=f"skill_{i}"):
                    selected.append(skill)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Next →", key="btn_skills", use_container_width=True):
                if not selected:
                    st.error("Please select at least one skill or click Skip!")
                else:
                    save_and_next("What skills do you have?", ", ".join(selected), "skills")
        with col2:
            if st.button("Skip → No skills yet", key="skip_skills", use_container_width=True):
                save_and_next("What skills do you have?", "No specific skills yet — willing to learn", "skills")


    # ─── Helper: Startup experience ──────────────────────────────────────────────
    def _show_startup_exp_question():
        st.markdown("🤖 **Do you have any previous startup experience?**")
        ans = st.selectbox("Your startup experience:", [
            "Select...", "No, this is my first idea",
            "Yes, worked in a startup", "Yes, co-founded a startup",
            "Yes, founded and exited",
            "Yes, founded but it failed — learned from it!"
        ], key="q_startup" ,label_visibility="collapsed")
        extra = ""
        if ans not in ["Select...", "No, this is my first idea"]:
            extra = st.text_area("Tell us about it (optional):",
                                 placeholder="e.g. I co-founded a food app in 2022...",
                                 height=70, key="q_startup_extra")
        if st.button("Next →", key="btn_startup"):
            if ans == "Select...":
                st.error("Please select an option!")
            else:
                full = f"{ans}. {extra}".strip(". ") if extra else ans
                save_and_next("Do you have any previous startup experience?", full, "startup_exp")


    # ─── Helper: Render chat history ─────────────────────────────────────────────
    def show_history():
        for item in st.session_state.chat_history:
            st.markdown(
                f"""<div style='background:#1e1e2e;padding:10px 14px;border-radius:12px;
                border-bottom-left-radius:2px;margin-bottom:4px;max-width:80%;color:#cdd6f4;'>
                🤖 {item['question']}</div>""",
                unsafe_allow_html=True
            )
            st.markdown(
                f"""<div style='background:#313244;padding:10px 14px;border-radius:12px;
                border-bottom-right-radius:2px;margin-bottom:16px;max-width:80%;
                margin-left:auto;color:#a6e3a1;text-align:right;'>
                👤 {item['answer'].replace(chr(10), '<br>')}</div>""",
                unsafe_allow_html=True
            )


    # ─── Show history + Back button ───────────────────────────────────────────────
    show_history()

    if st.session_state.chat_index > 0:
        if st.button("← Back", key="back_btn"):
            go_back()

    idx = st.session_state.chat_index
    data = st.session_state.founder_data
    bg  = data.get("background", "")
    sub = data.get("sub_field", "")

    is_special = bg in [
        "Self Taught / No Formal Education",
        "Just Have an Idea (No specific background)",
        "Complete Beginner (Nothing yet — just starting!)"
    ]

    # ══════════════════════════════════════════════════════════════════════════════
    # PERSONAL BLOCK — Q0 Name → Q1 Age → Q2 Location
    # ══════════════════════════════════════════════════════════════════════════════

    # Q0 — Name
    if idx == 0:
        st.markdown("🤖 **What is your name?**")
        ans = st.text_input("Your name:", placeholder="e.g. Abinash", key="q0_name", label_visibility="collapsed")
        if st.button("Next →", key="btn0"):
            if not ans.strip():
                st.error("Please enter your name!")
            else:
                save_and_next("What is your name?", ans.strip(), "founder_name")

    # Q1 — Age
    elif idx == 1:
        st.markdown("🤖 **What is your age range?**")
        ans = st.selectbox("Your age range:", ["Select...","Under 18", "18-22", "23-27", "28-35", "35-45", "45+"], key="q1_age", label_visibility="collapsed")
        if st.button("Next →", key="btn1"):
            if ans == "Select...":
                st.error("Please select an option!")
            else:
                save_and_next("What is your age range?", ans, "age")

    # Q2 — Location
    elif idx == 2:
        st.markdown("🤖 **Where are you based?**")
        col1, col2 = st.columns(2)
        with col1:
            country = st.selectbox("Country:", [
                "Select...", "India", "USA", "UK", "UAE", "Other"
            ], key="q2_country")
        with col2:
            city = st.text_input("City:", placeholder="e.g. Bhubaneswar", key="q2_city")
        if st.button("Next →", key="btn2"):
            if country == "Select..." or not city.strip():
                st.error("Please fill both country and city!")
            elif len(city.strip()) < 2:
                st.error("Please enter a valid city name!")
            elif not city.strip().replace(" ", "").isalpha():
                st.error("City name should only contain letters!")
            else:
                # Capitalize properly — "bhubaneswar" → "Bhubaneswar"
                clean_city = city.strip().title()
                save_and_next("Where are you based?", f"{clean_city}, {country}", "location")

    # ══════════════════════════════════════════════════════════════════════════════
    # PROFESSIONAL BLOCK — Q3 Background → Q4 Sub-field → Q5 Role → Q6 Skills
    # ══════════════════════════════════════════════════════════════════════════════

    # Q3 — Background
    elif idx == 3:
        st.markdown("🤖 **What best describes your background?**")
        ans = st.selectbox("Your background:", [
            "Select...",
            "Technical (Software / Data / Hardware etc.)",
            "Non-Technical (Arts / Teaching / Healthcare etc.)",
            "Business (Sales / Marketing / Finance etc.)",
            "Research (Science / Engineering / Social etc.)",
            "Student (School / College / Diploma)",
            "Creative (Design / Content / Media etc.)",
            "Self Taught / No Formal Education",
            "Just Have an Idea (No specific background)",
            "Complete Beginner (Nothing yet — just starting!)"
        ], key="q3" ,label_visibility="collapsed")
        if st.button("Next →", key="btn3"):
            if ans == "Select...":
                st.error("Please select an option!")
            else:
                save_and_next("What best describes your background?", ans, "background")

    # Q4 — Sub-field
    elif idx == 4:
        if "Non-Technical" not in bg and "Technical" in bg:
            st.markdown("🤖 **What is your technical field?**")
            ans = st.selectbox("Your technical field:", [
                "Select...",
                "Software Development (Web / Mobile)",
                "Data Science / AI / ML",
                "Hardware / Electronics / IoT",
                "Cybersecurity / Networking",
                "Cloud / DevOps / Infrastructure",
                "Blockchain / Web3",
                "Embedded Systems / Robotics",
                "Other Tech (General interest, not specialized)"
            ], key="q4_tech" ,label_visibility="collapsed")
            if st.button("Next →", key="btn4_tech"):
                if ans == "Select...":
                    st.error("Please select an option!")
                else:
                    save_and_next("What is your technical field?", ans, "sub_field")

        elif "Non-Technical" in bg:
            st.markdown("🤖 **What is your field?**")
            ans = st.selectbox("Your field:", [
                "Select...",
                "Arts / Design / Photography",
                "Teaching / Education / Coaching",
                "Healthcare / Nursing / Pharmacy",
                "Law / Legal Services",
                "Agriculture / Farming",
                "Hospitality / Tourism",
                "Social Work / NGO",
                "Other Non-Technical Field"
            ], key="q4_nontech" ,label_visibility="collapsed")
            if st.button("Next →", key="btn4_nontech"):
                if ans == "Select...":
                    st.error("Please select an option!")
                else:
                    save_and_next("What is your field?", ans, "sub_field")

        elif "Business" in bg:
            st.markdown("🤖 **What is your business field?**")
            ans = st.selectbox("Your business field:", [
                "Select...",
                "Sales / Business Development",
                "Marketing / Branding / PR",
                "Finance / Accounting / CA",
                "Operations / Supply Chain",
                "Management / Strategy",
                "Retail / E-commerce",
                "Import / Export / Trading",
                "Other Business Field"
            ], key="q4_biz" ,label_visibility="collapsed")
            if st.button("Next →", key="btn4_biz"):
                if ans == "Select...":
                    st.error("Please select an option!")
                else:
                    save_and_next("What is your business field?", ans, "sub_field")

        elif "Research" in bg:
            st.markdown("🤖 **What is your research field?**")
            ans = st.selectbox("Your research field:", [
                "Select...",
                "Science (Biology / Chemistry / Physics)",
                "Engineering / Material Science",
                "Medical / Clinical Research",
                "Social Science / Psychology",
                "Economics / Policy Research",
                "Environmental / Climate",
                "Space / Aerospace",
                "Other Research Field"
            ], key="q4_research" ,label_visibility="collapsed")
            if st.button("Next →", key="btn4_research"):
                if ans == "Select...":
                    st.error("Please select an option!")
                else:
                    save_and_next("What is your research field?", ans, "sub_field")

        elif "Student" in bg:
            st.markdown("🤖 **What is your current level?**")
            ans = st.selectbox("Your current level:", [
                "Select...",
                "School — 10th Grade",
                "School — 12th Grade",
                "Diploma",
                "Undergraduate (UG) — 1st / 2nd Year",
                "Undergraduate (UG) — 3rd / Final Year",
                "Postgraduate (PG)",
                "Dropout — Self Learning",
                "Dropout — Working"
            ], key="q4_student" ,label_visibility="collapsed")
            if st.button("Next →", key="btn4_student"):
                if ans == "Select...":
                    st.error("Please select an option!")
                else:
                    save_and_next("What is your current level?", ans, "sub_field")

        elif "Creative" in bg:
            st.markdown("🤖 **What is your creative field?**")
            ans = st.selectbox("Your creative field:", [
                "Select...",
                "UI / UX Design",
                "Graphic Design / Illustration",
                "Content Creation / YouTube / Blogging",
                "Photography / Videography",
                "Music / Audio Production",
                "Journalism / Media / Writing",
                "Animation / Motion Graphics",
                "Game Design",
                "Other Creative Field"
            ], key="q4_creative" ,label_visibility="collapsed")
            if st.button("Next →", key="btn4_creative"):
                if ans == "Select...":
                    st.error("Please select an option!")
                else:
                    save_and_next("What is your creative field?", ans, "sub_field")

        elif "Self Taught" in bg:
            st.markdown("🤖 **What have you taught yourself?**")
            ans = st.selectbox("What you taught yourself:", [
                "Select...",
                "Coding / Technology (self learned)",
                "Business / Trading / Sales (self learned)",
                "Design / Creative Skills (self learned)",
                "Multiple things — I learn what I need",
                "Still figuring out what to learn"
            ], key="q4_selftaught" ,label_visibility="collapsed")
            if st.button("Next →", key="btn4_selftaught"):
                if ans == "Select...":
                    st.error("Please select an option!")
                else:
                    save_and_next("What have you taught yourself?", ans, "sub_field")

        elif "Just Have an Idea" in bg:
            st.markdown("🤖 **Which area is your idea related to?**")
            ans = st.selectbox("Your idea area:", [
                "Select...",
                "Technology / App / Software",
                "Business / Service / Shop",
                "Social / Community / NGO",
                "Education / Coaching",
                "Health / Wellness",
                "Food / Agriculture",
                "Entertainment / Media",
                "Other area"
            ], key="q4_idea" ,label_visibility="collapsed")
            if st.button("Next →", key="btn4_idea"):
                if ans == "Select...":
                    st.error("Please select an option!")
                else:
                    save_and_next("Which area is your idea related to?", ans, "sub_field")

        elif "Complete Beginner" in bg:
            st.markdown("🤖 **That is totally okay! What sparked this idea for you?**")
            ans = st.selectbox("What sparked your idea:", [
                "Select...",
                "I faced a problem personally",
                "I saw someone else struggle with it",
                "I read / heard about it somewhere",
                "I just thought it could be a good business",
                "Not sure yet — just exploring"
            ], key="q4_beginner" ,label_visibility="collapsed")
            if st.button("Next →", key="btn4_beginner"):
                if ans == "Select...":
                    st.error("Please select an option!")
                else:
                    save_and_next("What sparked this idea for you?", ans, "sub_field")

    # Q5 — Role / Level
    elif idx == 5:
        if "Non-Technical" not in bg and "Technical" in bg:
            if sub == "Other Tech (General interest, not specialized)":
                q = "How would you describe your technical experience?"
                opts = [
                    "Select...",
                    "I just browse and use technology",
                    "I understand tech but cannot build yet",
                    "I have built small personal projects",
                    "I have real work / freelance experience",
                    "I am self taught with strong hands-on skills"
                ]
            else:
                q = "What is your current role?"
                opts = [
                    "Select...",
                    "Student (learning)",
                    "Fresher (0-1 year)",
                    "Junior (1-3 years)",
                    "Mid Level (3-5 years)",
                    "Senior (5+ years)",
                    "Freelancer / Independent"
                ]

        elif "Non-Technical" in bg:
            if "Arts" in sub or "Design" in sub or "Photography" in sub:
                q = "What is your experience level in Arts / Design?"
                opts = ["Select...", "Hobbyist (just for fun)",
                        "Semi-professional (some paid work)",
                        "Professional (full time / clients)",
                        "Freelancer / Self employed"]
            elif "Teaching" in sub or "Education" in sub or "Coaching" in sub:
                q = "What level do you teach or coach?"
                opts = ["Select...", "School level (K-12)",
                        "College / University level",
                        "Skill / Vocational training",
                        "Online coaching / Tutoring",
                        "Corporate training"]
            elif "Healthcare" in sub or "Nursing" in sub or "Pharmacy" in sub:
                q = "What is your role in healthcare?"
                opts = ["Select...", "Student (medical / nursing / pharmacy)",
                        "Paramedic / Technician",
                        "Nurse / Pharmacist",
                        "Doctor / Specialist",
                        "Healthcare Admin / Support"]
            elif "Law" in sub or "Legal" in sub:
                q = "What is your role in law / legal field?"
                opts = ["Select...", "Law student",
                        "Junior Associate / Paralegal",
                        "Practicing Lawyer",
                        "Legal Consultant",
                        "Judge / Senior Advocate"]
            elif "Agriculture" in sub or "Farming" in sub:
                q = "What is your role in agriculture?"
                opts = ["Select...", "Small farmer (personal / family)",
                        "Commercial farmer",
                        "Agricultural researcher / advisor",
                        "Agri-business owner",
                        "Government / NGO agriculture worker"]
            elif "Hospitality" in sub or "Tourism" in sub:
                q = "What is your role in hospitality / tourism?"
                opts = ["Select...", "Student (hotel management etc.)",
                        "Front line staff (hotel / restaurant)",
                        "Supervisor / Manager",
                        "Business owner (hotel / travel agency)",
                        "Tour guide / Freelancer"]
            elif "Social Work" in sub or "NGO" in sub:
                q = "What is your role in social work / NGO?"
                opts = ["Select...", "Volunteer",
                        "Field worker / Coordinator",
                        "Program manager",
                        "NGO founder / Co-founder",
                        "Government social worker"]
            else:
                q = "How long have you been in this field?"
                opts = ["Select...", "No experience yet",
                        "Less than 1 year", "1-3 years", "3-5 years", "5+ years"]

        elif "Business" in bg:
            q = "Do you currently run any business?"
            opts = ["Select...", "No, never ran a business",
                    "Yes, small informal business",
                    "Yes, registered company",
                    "Previously ran, now closed"]

        elif "Research" in bg:
            q = "What is your highest qualification?"
            opts = ["Select...", "Undergraduate (B.Sc / B.Tech)",
                    "Postgraduate (M.Sc / M.Tech)",
                    "PhD / Doctorate", "Post Doctorate",
                    "Industry Researcher (no formal degree)"]

        elif "Student" in bg:
            if sub == "School — 10th Grade":
                q = "What are you most interested in?"
                opts = ["Select...", "Computers / Technology", "Science / Math",
                        "Arts / Music", "Sports / Fitness", "Business / Money", "Not sure yet"]
            elif sub == "School — 12th Grade":
                q = "What stream are you in?"
                opts = ["Select...", "Science — PCM", "Science — PCB",
                        "Commerce (with Math)", "Commerce (without Math)", "Arts / Humanities"]
            elif sub == "Diploma":
                q = "What is your diploma field?"
                opts = ["Select...", "Computer Science / IT", "Mechanical",
                        "Electrical / Electronics", "Civil", "Design", "Business", "Other"]
            elif "UG" in sub:
                q = "What is your degree field?"
                opts = ["Select...", "Computer Science / IT", "Engineering (Non-CS)",
                        "Business / Commerce", "Science", "Arts / Humanities",
                        "Medical / Pharmacy", "Law", "Design", "Other"]
            elif sub == "Postgraduate (PG)":
                q = "What is your PG field?"
                opts = ["Select...", "Computer Science / MCA", "MBA",
                        "Science", "Arts", "Medical", "Law", "Design", "Other"]
            else:
                q = "What were you studying before?"
                opts = ["Select...", "Was in School", "College — Engineering",
                        "College — Non-Engineering", "Never formally studied", "Other"]

        elif "Creative" in bg:
            q = "Do you have a portfolio or online presence?"
            opts = ["Select...", "No portfolio yet", "Small personal portfolio",
                    "Active social media", "Published / Featured work",
                    "Professional portfolio with clients"]

        elif "Self Taught" in bg:
            q = "How long have you been self learning?"
            opts = ["Select...", "Just started (less than 6 months)",
                    "6 months to 1 year", "1-2 years", "3+ years",
                    "Many years — self taught is my lifestyle!"]

        elif "Just Have an Idea" in bg:
            q = "Have you done any research on this idea yet?"
            opts = ["Select...", "No, just thought of it",
                    "Yes, searched online a little",
                    "Yes, researched properly",
                    "Yes, and I have talked to people about it"]

        elif "Complete Beginner" in bg:
            q = "What do you feel most comfortable doing right now?"
            opts = ["Select...", "Talking to people / Networking",
                    "Learning new things online",
                    "Doing manual / physical work",
                    "Helping others / Problem solving",
                    "Nothing specific yet — I am figuring out"]

        else:
            q = "What is your experience level?"
            opts = ["Select...", "Beginner", "Intermediate", "Expert"]

        st.markdown(f"🤖 **{q}**")
        ans = st.selectbox("Your role:", opts, key="q5" ,label_visibility="collapsed")
        if st.button("Next →", key="btn5"):
            if ans == "Select...":
                st.error("Please select an option!")
            else:
                save_and_next(q, ans, "role_level")

    # Q6 — Skills
    elif idx == 6:
        _show_skills_question(bg)

    # ══════════════════════════════════════════════════════════════════════════════
    # Q7 — Real world exp (special) OR Startup exp (normal)
    # offset = 1 for special users only from here
    # ══════════════════════════════════════════════════════════════════════════════
    elif idx == 7:
        if is_special:
            st.markdown("🤖 **Do you have any real world experience — even without a degree?**")
            st.caption("e.g. ran a shop, did freelance work, helped in family business")
            ans = st.selectbox("Your experience:", [
                "Select...",
                "No experience at all — completely new",
                "Yes, helped in family business",
                "Yes, did small jobs / daily wage work",
                "Yes, ran a small informal business",
                "Yes, did freelance / gig work",
                "Yes, worked in a company (no degree needed role)",
                "Yes, have strong street / practical experience"
            ], key="q7_rw" ,label_visibility="collapsed")
            if st.button("Next →", key="btn7_rw"):
                if ans == "Select...":
                    st.error("Please select an option!")
                else:
                    save_and_next("Do you have any real world experience?", ans, "real_world_exp")
        else:
            _show_startup_exp_question()

    # ══════════════════════════════════════════════════════════════════════════════
    # Remaining questions — offset applies for special users
    # ══════════════════════════════════════════════════════════════════════════════
    offset = 1 if is_special else 0

    # Startup exp for special users
    if idx == 8 and is_special:
        _show_startup_exp_question()

    if idx == 8 + offset:
        st.markdown("🤖 **Have you talked to any real people about this idea yet?**")
        ans = st.selectbox("Your answer:", [
            "Select...", "No, not yet",
            "Yes, talked to friends / family",
            "Yes, talked to potential users",
            "Yes, already have people interested"
        ], key="q_userval" ,label_visibility="collapsed")
        if st.button("Next →", key="btn_userval"):
            if ans == "Select...":
                st.error("Please select an option!")
            else:
                save_and_next("Have you talked to any real people about this idea?", ans, "user_validation")

    elif idx == 9 + offset:
        st.markdown("🤖 **Do you know anyone who works in this industry?**")
        ans = st.selectbox("Your answer:", [
            "Select...", "No, I don't know anyone",
            "Yes, a few contacts",
            "Yes, strong industry connections",
            "I am already in this industry"
        ], key="q_network" ,label_visibility="collapsed")
        if st.button("Next →", key="btn_network"):
            if ans == "Select...":
                st.error("Please select an option!")
            else:
                save_and_next("Do you know anyone in this industry?", ans, "industry_network")

    elif idx == 10 + offset:
        st.markdown("🤖 **How much time can you give to this idea?**")
        ans = st.selectbox("Your answer:", [
            "Select...", "Full Time (8+ hours/day)",
            "Part Time (3-4 hours/day)",
            "Weekends Only",
            "Very Limited (1 hour/day)"
        ], key="q_time" ,label_visibility="collapsed")
        if st.button("Next →", key="btn_time"):
            if ans == "Select...":
                st.error("Please select an option!")
            else:
                save_and_next("How much time can you give?", ans, "available_time")

    elif idx == 11 + offset:
        st.markdown("🤖 **What is your main goal with this idea?**")
        ans = st.selectbox("Your answer:", [
            "Select...", "Make Money / Build a Business",
            "Solve a Real Problem I faced",
            "Build My Portfolio / Resume",
            "Get Incubated / Funded",
            "Learn and Explore",
            "Create Social Impact"
        ], key="q_goal" ,label_visibility="collapsed")
        if st.button("Next →", key="btn_goal"):
            if ans == "Select...":
                st.error("Please select an option!")
            else:
                save_and_next("What is your main goal?", ans, "main_goal")

    elif idx == 12 + offset:
        st.markdown("🤖 **Why THIS idea? What made you think of it?**")
        ans = st.text_area("Your answer:", placeholder="e.g. I personally faced this problem...",
                           height=80, key="q_why" ,label_visibility="collapsed")
        if st.button("Next →", key="btn_why"):
            if not ans.strip():
                st.error("Please type your answer!")
            else:
                save_and_next("Why this idea?", ans.strip(), "motivation")

    elif idx == 13 + offset:
        st.markdown("🤖 **Have you already tried anything to work on this idea? (optional)**")
        ans = st.text_area("Your answer:", placeholder="e.g. I built a rough prototype...",
                           height=80, key="q_tried" ,label_visibility="collapsed")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Next →", key="btn_tried", use_container_width=True):
                if not ans.strip():
                    st.error("Please type your answer or click Skip!")
                else:
                    save_and_next("Have you already tried anything?", ans.strip(), "already_tried")
        with col2:
            if st.button("Skip →", key="skip_tried", use_container_width=True):
                save_and_next("Have you already tried anything?",
                              "Nothing tried yet — idea is still in thinking stage", "already_tried")

    elif idx == 14 + offset:
        st.markdown("🤖 **What is your biggest fear about this idea? (optional)**")
        ans = st.text_area("Your answer:", placeholder="e.g. I am worried about competition...",
                           height=80, key="q_fear" ,label_visibility="collapsed")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Next →", key="btn_fear", use_container_width=True):
                if not ans.strip():
                    st.error("Please type your answer or click Skip!")
                else:
                    save_and_next("Biggest fear?", ans.strip(), "biggest_fear")
        with col2:
            if st.button("Skip →", key="skip_fear", use_container_width=True):
                save_and_next("Biggest fear?", "No specific fear mentioned by user", "biggest_fear")

    elif idx == 15 + offset:
        st.markdown("🤖 **Anything else about yourself you want to share? (optional)**")
        ans = st.text_area("Your answer:", placeholder="e.g. I am a 2nd year CS student...",
                           height=100, key="q_about" ,label_visibility="collapsed")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Done ✅", key="btn_about", use_container_width=True):
                if not ans.strip():
                    st.error("Please type something or click Skip!")
                else:
                    save_and_next("Anything else about yourself?", ans.strip(), "about_self")
        with col2:
            if st.button("Skip →", key="skip_about", use_container_width=True):
                save_and_next("Anything else about yourself?",
                              "No additional info provided by user", "about_self")

    elif idx >= 16 + offset:
        st.session_state.founder_name = st.session_state.founder_data.get("founder_name", "")
        
         # ── Run Tavily once here — stored for Step 3 AND Step 4 ──
        if st.session_state.search_context is None:
            with st.spinner("🔍 Researching the market for your idea..."):
                st.session_state.search_context = get_search_context(
                    st.session_state.idea,
                    st.session_state.founder_data
                )
        st.session_state.step = 3
        st.rerun()

# ─── Step 3: Adaptive Questions ──────────────────────────────────────────────

elif st.session_state.step == 3:
    st.header("❓ Step 3: Let's Talk About Your Idea!")
    st.divider()

    current_index = st.session_state.current_question_index
    history = st.session_state.answers_history

    # Generate current question if not already generated
    if len(st.session_state.questions) <= current_index:
        with st.spinner("⏳ Thinking..."):
            question = generate_single_question(
            st.session_state.idea,
            st.session_state.founder_name,
            st.session_state.founder_data,
            history,
            st.session_state.search_context
        )
            st.session_state.questions.append(question)

    # Show current question
    current_question = st.session_state.questions[current_index]

    st.divider()
    st.write(f"### 💬 {current_question}")
    st.write("")
    st.write("*You can type your answer below or click 'I Don't Know' if you are unsure!*")

    answer = st.text_area(
        "Your Answer:",
        height=120,
        key=f"answer_{current_index}",
        placeholder="Type your answer here... don't worry, there are no wrong answers!"
    )

    st.write("**OR**")

    # ── Helper Function ──
    def step3_save_and_next(ans):
        st.session_state.answers_history.append({
            "question": current_question,
            "answer": ans
        })
        if current_index < 3:
            st.session_state.current_question_index += 1
        else:
            st.session_state.followup_qa = st.session_state.answers_history
            st.session_state.step = 4
        st.rerun()

    # ── Buttons ──
    col1, col2 = st.columns(2)

    with col1:
        if current_index < 3:
            if st.button("Next →", key=f"btn_q{current_index}", use_container_width=True):
                if not answer.strip():
                    st.error("❌ Please type your answer or click I Don't Know!")
                else:
                    step3_save_and_next(answer)
        else:
            if st.button("Analyze My Idea 🚀", key="btn_analyze", use_container_width=True):
                if not answer.strip():
                    st.error("❌ Please type your answer or click I Don't Know!")
                else:
                    step3_save_and_next(answer)

    with col2:
        if st.button("🤷 I Don't Know", key=f"btn_idk_{current_index}", use_container_width=True):
            step3_save_and_next("I don't know")


# ─── Step 4: Analysis & Results ──────────────────────────────────────────────

elif st.session_state.step == 4:
    st.header("🧠 Step 4: Analysis Results")
    st.divider()

    if st.session_state.analysis is None:
        MAX_RETRIES = 3
        attempt = 0
        success = False
        analysis = None

        with st.spinner("⏳ Analyzing your idea... This may take a few seconds..."):
            while attempt < MAX_RETRIES:
                analysis = analyze_idea(
                    st.session_state.idea,
                    st.session_state.founder_name,
                    st.session_state.founder_data,
                    st.session_state.followup_qa,
                    st.session_state.search_context
                )
                grade = grade_output(analysis)

                try:
                    score = int(grade.get("quality_score", 0))
                except (ValueError, TypeError):
                    score = 0
                if score >= 3 and grade.get("feedback", "").strip():
                    success = True
                    break

                attempt += 1

        if not success:
            st.error("❌ Analysis failed after 3 attempts. Please try again.")

            if st.button("🏠 Start Over"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

            st.stop()

        analysis["founder_profile"] = st.session_state.founder_data
        analysis["followup_qa"] = st.session_state.followup_qa
        analysis["original_idea"] = st.session_state.idea
        analysis["search_context"] = st.session_state.search_context
        st.session_state.analysis = analysis

    # ─── Save to MongoDB ──────────────────────────────────────────────
        save_analysis(analysis)

    analysis = st.session_state.analysis

    # ─── Normal Report Page ───────────────────────────────────────────────
    if st.session_state.sub_page is None:

        # ─── Summary ─────────────────────────────────────────────────────
        st.subheader("📊 Overall Summary")
        st.write(f"**Founder:** {analysis.get('founder_name', 'N/A')}")
        st.write(f"**Idea:** {analysis.get('idea_summary', 'N/A')}")
        st.write(f"**Overall Score:** {analysis.get('overall', {}).get('score', 'N/A')}/10")

        mvp_status = analysis.get('overall', {}).get('is_mvp_ready', 'N/A')
        st.write(f"**MVP Ready:** {mvp_status}")
        if "no" in str(mvp_status).lower():
            if st.button("🔧 How to make it MVP Ready?", key="btn_mvp_help"):
                st.session_state.sub_page = "mvp_help"
                st.rerun()

        investment_status = analysis.get('overall', {}).get('is_investment_ready', 'N/A')
        st.write(f"**Investment Ready:** {investment_status}")
        if "no" in str(investment_status).lower():
            if st.button("💰 How to make it Investment Ready?", key="btn_investment_help"):
                st.session_state.sub_page = "investment_help"
                st.rerun()

        st.write(f"**Incubator Ready:** {analysis.get('overall', {}).get('is_incubator_ready', 'N/A')}")
        st.divider()

        # ─── Scores ──────────────────────────────────────────────────────
        st.subheader("⭐ Scores (1-10)")
        scores = analysis.get("scores", {})
        for category, data in scores.items():
            st.write(f"**{category.replace('_', ' ').title()}:** {data.get('score', 'N/A')}/10")
            st.write(f"_{data.get('reasoning', 'N/A')}_")
        st.divider()

        # ─── Problem Statement ────────────────────────────────────────────
        st.subheader("🎯 Problem Statement")
        problem = analysis.get("problem_statement", {})

        st.write(f"**Description:** {problem.get('description', 'N/A')}")
        st.write(f"**Target Audience:** {problem.get('target_audience', 'N/A')}")
        st.write(f"**Why Current Solutions Fail:** {problem.get('why_current_solutions_fail', 'N/A')}")
        st.write(f"**Who Suffers Most:** {problem.get('who_suffers_most', 'N/A')}")
        st.write(f"**How Long Problem Exists:** {problem.get('how_long_problem_exists', 'N/A')}")
        st.write(f"**Market Size:** {problem.get('market_size_hint', 'N/A')}")
        st.write(f"**Current Workarounds:** {problem.get('current_workarounds', 'N/A')}")

        st.write("**📖 Real World Example:**")
        st.info(problem.get("real_world_example", "N/A"))

        st.write("**😣 Pain Points:**")
        for point in problem.get("pain_points", []):
            st.write(f"• {point}")
        st.divider()

        # ─── Proposed Solution ────────────────────────────────────────────
        st.subheader("💡 Proposed Solution")
        solution = analysis.get("proposed_solution", {})

        st.info(f"🎯 **One Line Pitch:** {solution.get('one_line_pitch', 'N/A')}")

        st.write("**Simple Explanation:**")
        st.write(solution.get("simple_explanation", "N/A"))

        st.write("**🔧 How It Works — Step by Step:**")
        for i, step in enumerate(solution.get("step_by_step_how_it_works", []), 1):
            st.write(f"{i}. {step}")

        st.write("**⭐ Key Features:**")
        for feature in solution.get("key_features", []):
            st.write(f"• {feature}")

        st.write(f"**💪 Unfair Advantage:** {solution.get('unfair_advantage', 'N/A')}")
        st.divider()

        # ─── Core Innovation ──────────────────────────────────────────────────────
        st.subheader("💡 Core Innovation")
        innovation = analysis.get("core_innovation", {})
        st.write(f"**Uniqueness:** {innovation.get('uniqueness', 'N/A')}")
        st.write(f"**Innovation Type:** {innovation.get('innovation_type', 'N/A')}")
        st.divider()

        # ─── Market Landscape ─────────────────────────────────────────────────────
        st.subheader("🌍 Market Landscape")
        market = analysis.get("market_landscape", {})
        st.write(f"**Similar Solutions:** {market.get('similar_solutions', 'N/A')}")
        st.write(f"**Competition Level:** {market.get('competition_level', 'N/A')}")
        st.write(f"**Market Gap:** {market.get('market_gap', 'N/A')}")
        st.divider()

        # ─── Support Required ─────────────────────────────────────────────────────
        st.subheader("🤝 Support Required")
        support = analysis.get("support_required", {})
        st.write(f"**Team Needed:** {support.get('team_needed', 'N/A')}")
        st.write(f"**Funding Stage:** {support.get('funding_stage', 'N/A')}")
        st.write(f"**Partnerships:** {support.get('partnerships', 'N/A')}")
        st.write(f"**Regulatory:** {support.get('regulatory', 'N/A')}")
        st.divider()

        # ─── Tech Stack ───────────────────────────────────────────────────────────
        st.subheader("🛠️ Tech Stack")
        tech = analysis.get("tech_stack", {})
        st.write(f"**Backend:** {tech.get('backend', 'N/A')}")
        st.write(f"**Frontend:** {tech.get('frontend', 'N/A')}")
        st.write(f"**Database:** {tech.get('database', 'N/A')}")
        st.write(f"**Cloud:** {tech.get('cloud', 'N/A')}")
        st.write(f"**AI Tools:** {tech.get('ai_tools', 'N/A')}")
        st.divider()

        # ─── Download Buttons ─────────────────────────────────────────────
        st.subheader("📥 Download ")

        if "report_paths" not in st.session_state:
            json_content = save_json(analysis)
            md_content = save_markdown(analysis)
            st.session_state.report_paths = {"json": json_content, "md": md_content}

        json_content = st.session_state.report_paths["json"]
        md_content = st.session_state.report_paths["md"]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button(
                label="📦 Download JSON",
                data=json_content,
                file_name="analysis.json",
                mime="application/json",
                use_container_width=True
            )
        with col2:
            st.download_button(
                label="📄 Download Report",
                data=md_content,
                file_name="report.md",
                mime="text/markdown",
                use_container_width=True
            )
        with col3:
            if "ppt_bytes" not in st.session_state:
                if st.button("🎯 Generate Pitch Deck", use_container_width=True):
                    with st.spinner("⏳ Building your pitch deck..."):
                        ppt_bytes = generate_ppt(st.session_state.analysis)
                        st.session_state.ppt_bytes = ppt_bytes
                        st.rerun()
                
            else:
                st.download_button(
                    label="⬇️ Download Pitch Deck (.pptx)",
                    data=st.session_state.ppt_bytes,
                    file_name="pitch_deck.pptx",
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    use_container_width=True
                )
        st.divider()

        # ─── Start Over ───────────────────────────────────────────────────
        if st.button("🔄 Start Over"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # ─── MVP Help Page ────────────────────────────────────────────────────
    elif st.session_state.sub_page == "mvp_help":
        st.header("🔧 How to Make Your Idea MVP Ready")
        st.caption("These are AI generated steps specifically for your idea")
        st.divider()

        if "mvp_tips" not in st.session_state:
            with st.spinner("⏳ Generating your MVP roadmap..."):
                for attempt in range(3):
                    tips = generate_readiness_tips(
                        st.session_state.analysis,
                        "mvp",
                        st.session_state.search_context
                    )
                    if tips.get("what_it_means") and tips.get("steps_to_become_ready"):
                        break
                st.session_state.mvp_tips = tips

        tips = st.session_state.mvp_tips

        st.subheader("📌 What MVP means for your idea")
        st.info(tips.get("what_it_means", "N/A"))

        st.subheader("❌ Why it is not MVP Ready yet")
        for point in tips.get("why_not_ready", []):
            st.write(f"• {point}")

        st.subheader("✅ Steps to become MVP Ready")
        for i, step in enumerate(tips.get("steps_to_become_ready", []), 1):
            st.write(f"**{i}.** {step}")

        st.subheader("⏰ Realistic Timeline")
        st.write(tips.get("realistic_timeline", "N/A"))

        st.subheader("🚀 First thing to do tomorrow")
        st.success(tips.get("first_action", "N/A"))
        st.divider()

        if st.button("← Back to Report", key="back_from_mvp"):
            st.session_state.sub_page = None
            st.rerun()

    # ─── Investment Help Page ─────────────────────────────────────────────
    elif st.session_state.sub_page == "investment_help":
        st.header("💰 How to Make Your Idea Investment Ready")
        st.caption("These are AI generated steps specifically for your idea")
        st.divider()

        if "investment_tips" not in st.session_state:
            with st.spinner("⏳ Generating your Investment roadmap..."):
                for attempt in range(3):
                    tips = generate_readiness_tips(
                        st.session_state.analysis,
                        "investment",
                        st.session_state.search_context
                    )
                    if tips.get("what_it_means") and tips.get("steps_to_become_ready"):
                        break
                st.session_state.investment_tips = tips

        tips = st.session_state.investment_tips

        st.subheader("📌 What Investment Ready means")
        st.info(tips.get("what_it_means", "N/A"))

        st.subheader("❌ Why it is not Investment Ready yet")
        for point in tips.get("why_not_ready", []):
            st.write(f"• {point}")

        st.subheader("✅ Steps to become Investment Ready")
        for i, step in enumerate(tips.get("steps_to_become_ready", []), 1):
            st.write(f"**{i}.** {step}")

        st.subheader("👀 What Investors Look For")
        for point in tips.get("what_investors_look_for", []):
            st.write(f"• {point}")

        st.subheader("⏰ Realistic Timeline")
        st.write(tips.get("realistic_timeline", "N/A"))

        st.subheader("🚀 First thing to do tomorrow")
        st.success(tips.get("first_action", "N/A"))
        st.divider()

        if st.button("← Back to Report", key="back_from_investment"):
            st.session_state.sub_page = None
            st.rerun()