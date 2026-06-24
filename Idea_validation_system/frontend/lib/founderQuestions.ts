/**
 * lib/founderQuestions.ts
 * All founder profile questions ported from app.py Step 2 logic.
 * Questions are evaluated in order; each has an optional `condition`
 * that controls whether it appears based on prior answers.
 */

export type QuestionType = "text" | "select" | "checkbox" | "textarea";

export interface Question {
  key: string;
  type: QuestionType;
  label: string;
  placeholder?: string;
  options?: string[];
  condition?: (data: Record<string, any>) => boolean;
  allowSkip?: boolean;
  skipValue?: string;
  caption?: string;
}

const always = () => true;
const hasBg = (bg: string) => (d: Record<string, any>) =>
  (d.background || "").includes(bg);
const notBg = (bg: string) => (d: Record<string, any>) =>
  !(d.background || "").includes(bg);
const isSpecial = (d: Record<string, any>) =>
  [
    "Self Taught / No Formal Education",
    "Just Have an Idea (No specific background)",
    "Complete Beginner (Nothing yet — just starting!)",
  ].includes(d.background || "");

// ─── Builds the flat ordered list of questions, filtered by conditions ────────
export function getActiveQuestions(
  data: Record<string, any>
): Question[] {
  return ALL_QUESTIONS.filter((q) => (q.condition ?? always)(data));
}

// ─── All questions (in order) ─────────────────────────────────────────────────
export const ALL_QUESTIONS: Question[] = [
  // Q0 — Name
  {
    key: "founder_name",
    type: "text",
    label: "What is your name?",
    placeholder: "e.g. Abinash",
    condition: always,
  },
  // Q1 — Age
  {
    key: "age",
    type: "select",
    label: "What is your age range?",
    options: ["Under 18", "18–22", "23–27", "28–35", "35–45", "45+"],
    condition: always,
  },
  // Q2 — Location (handled specially as two fields — see profile.tsx)
  {
    key: "location",
    type: "select",
    label: "Where are you based?",
    options: ["India", "USA", "UK", "UAE", "Other"],
    condition: always,
  },
  // Q3 — Background
  {
    key: "background",
    type: "select",
    label: "What best describes your background?",
    options: [
      "Technical (Software / Data / Hardware etc.)",
      "Non-Technical (Arts / Teaching / Healthcare etc.)",
      "Business (Sales / Marketing / Finance etc.)",
      "Research (Science / Engineering / Social etc.)",
      "Student (School / College / Diploma)",
      "Creative (Design / Content / Media etc.)",
      "Self Taught / No Formal Education",
      "Just Have an Idea (No specific background)",
      "Complete Beginner (Nothing yet — just starting!)",
    ],
    condition: always,
  },
  // Q4 — Sub-field (varies by background)
  {
    key: "sub_field",
    type: "select",
    label: "What is your technical field?",
    options: [
      "Software Development (Web / Mobile)",
      "Data Science / AI / ML",
      "Hardware / Electronics / IoT",
      "Cybersecurity / Networking",
      "Cloud / DevOps / Infrastructure",
      "Blockchain / Web3",
      "Embedded Systems / Robotics",
      "Other Tech (General interest, not specialized)",
    ],
    condition: (d) =>
      (d.background || "").includes("Technical") &&
      !(d.background || "").includes("Non-Technical"),
  },
  {
    key: "sub_field",
    type: "select",
    label: "What is your field?",
    options: [
      "Arts / Design / Photography",
      "Teaching / Education / Coaching",
      "Healthcare / Nursing / Pharmacy",
      "Law / Legal Services",
      "Agriculture / Farming",
      "Hospitality / Tourism",
      "Social Work / NGO",
      "Other Non-Technical Field",
    ],
    condition: hasBg("Non-Technical"),
  },
  {
    key: "sub_field",
    type: "select",
    label: "What is your business field?",
    options: [
      "Sales / Business Development",
      "Marketing / Branding / PR",
      "Finance / Accounting / CA",
      "Operations / Supply Chain",
      "Management / Strategy",
      "Retail / E-commerce",
      "Import / Export / Trading",
      "Other Business Field",
    ],
    condition: hasBg("Business"),
  },
  {
    key: "sub_field",
    type: "select",
    label: "What is your research field?",
    options: [
      "Science (Biology / Chemistry / Physics)",
      "Engineering / Material Science",
      "Medical / Clinical Research",
      "Social Science / Psychology",
      "Economics / Policy Research",
      "Environmental / Climate",
      "Space / Aerospace",
      "Other Research Field",
    ],
    condition: hasBg("Research"),
  },
  {
    key: "sub_field",
    type: "select",
    label: "What is your current level?",
    options: [
      "School — 10th Grade",
      "School — 12th Grade",
      "Diploma",
      "Undergraduate (UG) — 1st / 2nd Year",
      "Undergraduate (UG) — 3rd / Final Year",
      "Postgraduate (PG)",
      "Dropout — Self Learning",
      "Dropout — Working",
    ],
    condition: hasBg("Student"),
  },
  {
    key: "sub_field",
    type: "select",
    label: "What is your creative field?",
    options: [
      "UI / UX Design",
      "Graphic Design / Illustration",
      "Content Creation / YouTube / Blogging",
      "Photography / Videography",
      "Music / Audio Production",
      "Journalism / Media / Writing",
      "Animation / Motion Graphics",
      "Game Design",
      "Other Creative Field",
    ],
    condition: hasBg("Creative"),
  },
  {
    key: "sub_field",
    type: "select",
    label: "What have you taught yourself?",
    options: [
      "Coding / Technology (self learned)",
      "Business / Trading / Sales (self learned)",
      "Design / Creative Skills (self learned)",
      "Multiple things — I learn what I need",
      "Still figuring out what to learn",
    ],
    condition: hasBg("Self Taught"),
  },
  {
    key: "sub_field",
    type: "select",
    label: "Which area is your idea related to?",
    options: [
      "Technology / App / Software",
      "Business / Service / Shop",
      "Social / Community / NGO",
      "Education / Coaching",
      "Health / Wellness",
      "Food / Agriculture",
      "Entertainment / Media",
      "Other area",
    ],
    condition: hasBg("Just Have an Idea"),
  },
  {
    key: "sub_field",
    type: "select",
    label: "That's totally okay! What sparked this idea for you?",
    options: [
      "I faced a problem personally",
      "I saw someone else struggle with it",
      "I read / heard about it somewhere",
      "I just thought it could be a good business",
      "Not sure yet — just exploring",
    ],
    condition: hasBg("Complete Beginner"),
  },
  // Q5 — Role/Level
  {
    key: "role_level",
    type: "select",
    label: "What is your current role?",
    options: [
      "Student (learning)",
      "Fresher (0–1 year)",
      "Junior (1–3 years)",
      "Mid Level (3–5 years)",
      "Senior (5+ years)",
      "Freelancer / Independent",
    ],
    condition: (d) =>
      (d.background || "").includes("Technical") &&
      !(d.background || "").includes("Non-Technical") &&
      d.sub_field !== "Other Tech (General interest, not specialized)",
  },
  {
    key: "role_level",
    type: "select",
    label: "How would you describe your technical experience?",
    options: [
      "I just browse and use technology",
      "I understand tech but cannot build yet",
      "I have built small personal projects",
      "I have real work / freelance experience",
      "I am self taught with strong hands-on skills",
    ],
    condition: (d) =>
      (d.background || "").includes("Technical") &&
      !(d.background || "").includes("Non-Technical") &&
      d.sub_field === "Other Tech (General interest, not specialized)",
  },
  {
    key: "role_level",
    type: "select",
    label: "What is your experience level in your non-technical field?",
    options: [
      "No experience yet",
      "Less than 1 year",
      "1–3 years",
      "3–5 years",
      "5+ years",
    ],
    condition: hasBg("Non-Technical"),
  },
  {
    key: "role_level",
    type: "select",
    label: "Do you currently run any business?",
    options: [
      "No, never ran a business",
      "Yes, small informal business",
      "Yes, registered company",
      "Previously ran, now closed",
    ],
    condition: hasBg("Business"),
  },
  {
    key: "role_level",
    type: "select",
    label: "What is your highest qualification?",
    options: [
      "Undergraduate (B.Sc / B.Tech)",
      "Postgraduate (M.Sc / M.Tech)",
      "PhD / Doctorate",
      "Post Doctorate",
      "Industry Researcher (no formal degree)",
    ],
    condition: hasBg("Research"),
  },
  {
    key: "role_level",
    type: "select",
    label: "Do you have a portfolio or online presence?",
    options: [
      "No portfolio yet",
      "Small personal portfolio",
      "Active social media",
      "Published / Featured work",
      "Professional portfolio with clients",
    ],
    condition: hasBg("Creative"),
  },
  {
    key: "role_level",
    type: "select",
    label: "How long have you been self learning?",
    options: [
      "Just started (less than 6 months)",
      "6 months to 1 year",
      "1–2 years",
      "3+ years",
      "Many years — self taught is my lifestyle!",
    ],
    condition: hasBg("Self Taught"),
  },
  {
    key: "role_level",
    type: "select",
    label: "Have you done any research on this idea yet?",
    options: [
      "No, just thought of it",
      "Yes, searched online a little",
      "Yes, researched properly",
      "Yes, and I have talked to people about it",
    ],
    condition: hasBg("Just Have an Idea"),
  },
  {
    key: "role_level",
    type: "select",
    label: "What do you feel most comfortable doing right now?",
    options: [
      "Talking to people / Networking",
      "Learning new things online",
      "Doing manual / physical work",
      "Helping others / Problem solving",
      "Nothing specific yet — I am figuring out",
    ],
    condition: hasBg("Complete Beginner"),
  },
  {
    key: "role_level",
    type: "select",
    label: "What is your current level of education?",
    options: [
      "School — 10th Grade",
      "School — 12th Grade",
      "Undergraduate",
      "Postgraduate",
      "Dropout",
    ],
    condition: (d) => !d.background,
  },
  // Q6 — Skills (checkbox)
  {
    key: "skills",
    type: "checkbox",
    label: "What skills do you have? (Select all that apply)",
    condition: always,
    allowSkip: true,
    skipValue: "No specific skills yet — willing to learn",
  },
  // Q7 — Real world experience (special users only)
  {
    key: "real_world_exp",
    type: "select",
    label: "Do you have any real world experience — even without a degree?",
    caption: "e.g. ran a shop, did freelance work, helped in family business",
    options: [
      "No experience at all — completely new",
      "Yes, helped in family business",
      "Yes, did small jobs / daily wage work",
      "Yes, ran a small informal business",
      "Yes, did freelance / gig work",
      "Yes, worked in a company (no degree needed role)",
      "Yes, have strong street / practical experience",
    ],
    condition: isSpecial,
  },
  // Q8 — Startup experience
  {
    key: "startup_exp",
    type: "select",
    label: "Do you have any previous startup experience?",
    options: [
      "No, this is my first idea",
      "Yes, worked in a startup",
      "Yes, co-founded a startup",
      "Yes, founded and exited",
      "Yes, founded but it failed — learned from it!",
    ],
    condition: always,
  },
  // Q9 — User validation
  {
    key: "user_validation",
    type: "select",
    label: "Have you talked to any real people about this idea yet?",
    options: [
      "No, not yet",
      "Yes, talked to friends / family",
      "Yes, talked to potential users",
      "Yes, already have people interested",
    ],
    condition: always,
  },
  // Q10 — Industry network
  {
    key: "industry_network",
    type: "select",
    label: "Do you know anyone who works in this industry?",
    options: [
      "No, I don't know anyone",
      "Yes, a few contacts",
      "Yes, strong industry connections",
      "I am already in this industry",
    ],
    condition: always,
  },
  // Q11 — Time
  {
    key: "available_time",
    type: "select",
    label: "How much time can you give to this idea?",
    options: [
      "Full Time (8+ hours/day)",
      "Part Time (3–4 hours/day)",
      "Weekends Only",
      "Very Limited (1 hour/day)",
    ],
    condition: always,
  },
  // Q12 — Goal
  {
    key: "main_goal",
    type: "select",
    label: "What is your main goal with this idea?",
    options: [
      "Make Money / Build a Business",
      "Solve a Real Problem I faced",
      "Build My Portfolio / Resume",
      "Get Incubated / Funded",
      "Learn and Explore",
      "Create Social Impact",
    ],
    condition: always,
  },
  // Q13 — Motivation
  {
    key: "motivation",
    type: "textarea",
    label: "Why THIS idea? What made you think of it?",
    placeholder: "e.g. I personally faced this problem...",
    condition: always,
  },
  // Q14 — Already tried
  {
    key: "already_tried",
    type: "textarea",
    label: "Have you already tried anything to work on this idea? (optional)",
    placeholder: "e.g. I built a rough prototype...",
    condition: always,
    allowSkip: true,
    skipValue: "Nothing tried yet — idea is still in thinking stage",
  },
  // Q15 — Fear
  {
    key: "biggest_fear",
    type: "textarea",
    label: "What is your biggest fear about this idea? (optional)",
    placeholder: "e.g. I am worried about competition...",
    condition: always,
    allowSkip: true,
    skipValue: "No specific fear mentioned",
  },
  // Q16 — About self
  {
    key: "about_self",
    type: "textarea",
    label: "Anything else about yourself you want to share? (optional)",
    placeholder: "e.g. I am a 2nd year CS student...",
    condition: always,
    allowSkip: true,
    skipValue: "No additional info provided",
  },
];

// Skills map by background + sub_field
export const SKILLS_MAP: Record<string, string[]> = {
  Technical: [
    "Python / Programming","Web Development","Mobile App Dev",
    "Machine Learning / AI","Cloud / DevOps","Database / SQL",
    "Cybersecurity","UI / UX Design","System Design","GitHub / Open Source",
  ],
  "Hardware / Electronics / IoT": [
    "Circuit Design / PCB","Embedded Systems (Arduino / ESP32)","Sensor Integration",
    "3D Printing / CAD","Robotics / Servo Control","Firmware / RTOS",
    "IoT Protocols (MQTT / BLE / WiFi)","Hardware Prototyping",
    "Electronics Repair / Debugging","Lab Testing / Measurement",
  ],
  "Embedded Systems / Robotics": [
    "Embedded C / C++","RTOS (FreeRTOS / Zephyr)","Robotics (ROS / ROS2)",
    "Motor / Servo Control","Sensor Fusion","PCB Design",
    "Real-time Control Systems","CAN / I2C / SPI / UART",
    "Computer Vision (Edge)","Hardware Debugging",
  ],
  "Cybersecurity / Networking": [
    "Network Security","Penetration Testing","Linux / Shell Scripting",
    "Firewall / VPN Setup","Cryptography","Incident Response",
    "SIEM Tools","Cloud Security","Web App Security","Ethical Hacking",
  ],
  "Cloud / DevOps / Infrastructure": [
    "AWS / GCP / Azure","Docker / Kubernetes","CI / CD Pipelines",
    "Infrastructure as Code (Terraform)","Linux Server Admin",
    "Monitoring / Logging (Grafana)","Bash / Python Scripting",
    "Database Admin","Networking (DNS / Load Balancing)","Site Reliability",
  ],
  "Data Science / AI / ML": [
    "Python (NumPy / Pandas)","Machine Learning (sklearn / PyTorch)","Deep Learning",
    "Data Visualization","SQL / Data Wrangling","NLP / LLMs",
    "Computer Vision","MLOps / Model Deployment","Statistical Analysis","Big Data (Spark)",
  ],
  "Blockchain / Web3": [
    "Solidity / Smart Contracts","Web3.js / Ethers.js","DeFi Protocols",
    "NFT Development","Wallet Integration","IPFS / Decentralized Storage",
    "Tokenomics Design","Audit / Security","Layer 2 Solutions","DAO Governance",
  ],
  "Non-Technical": [
    "Communication / Speaking","Teaching / Training","Writing / Storytelling",
    "Community Building","Event Management","Customer Handling",
    "Field Research","Photography / Video","Social Media","Language Skills",
  ],
  Business: [
    "Sales / Cold Calling","Digital Marketing","Finance / Budgeting",
    "Business Planning","Negotiation","Team Leadership",
    "Networking","Pitching","E-commerce","Legal Basics",
  ],
  Research: [
    "Data Collection","Statistical Analysis","Academic Writing",
    "Lab / Experimental Work","Python / R","Grant Writing",
    "Patent Filing","Public Speaking","Teaching","Policy Writing",
  ],
  Student: [
    "Basic Coding","MS Office / Google Docs","Social Media",
    "Research / Googling","Public Speaking","Event Organizing",
    "Content Writing","Basic Design (Canva)","Video Editing","Freelancing",
  ],
  Creative: [
    "UI / UX (Figma)","Graphic Design","Video Editing",
    "Photography","Copywriting","Social Media Growth",
    "Branding","Motion Graphics","Music Production","Freelance Work",
  ],
  "Self Taught": [
    "Self Taught Coding","Self Taught Business Skills","Self Taught Design",
    "YouTube / Online Courses","Hands-on Project Experience",
    "Community / Network Building","Problem Solving","Resourcefulness",
    "Learning Fast","Street Smart",
  ],
  "Just Idea": [
    "Common Sense / Observation","Communication","Networking",
    "Research / Reading","Problem Spotting","Convincing Others",
    "Basic Computer Use","Social Media","Managing People","Street Smart",
  ],
  Beginner: [
    "Willingness to Learn","Common Sense","Communication",
    "Hard Work / Dedication","Social Media (basic)","Basic Computer Use",
    "Observation Skills","Helping Others","Street Smart",
    "Nothing specific yet — and that is okay!",
  ],
};

export function getSkillsForBackground(bg: string, subField?: string): string[] {
  if (bg.includes("Non-Technical")) return SKILLS_MAP["Non-Technical"];
  if (bg.includes("Technical") && !bg.includes("Non-Technical")) {
    // Use sub_field to pick the right technical skills list
    if (subField?.includes("Hardware") || subField?.includes("IoT"))
      return SKILLS_MAP["Hardware / Electronics / IoT"];
    if (subField?.includes("Embedded") || subField?.includes("Robotics"))
      return SKILLS_MAP["Embedded Systems / Robotics"];
    if (subField?.includes("Cybersecurity") || subField?.includes("Networking"))
      return SKILLS_MAP["Cybersecurity / Networking"];
    if (subField?.includes("Cloud") || subField?.includes("DevOps"))
      return SKILLS_MAP["Cloud / DevOps / Infrastructure"];
    if (subField?.includes("Data") || subField?.includes("AI") || subField?.includes("ML"))
      return SKILLS_MAP["Data Science / AI / ML"];
    if (subField?.includes("Blockchain") || subField?.includes("Web3"))
      return SKILLS_MAP["Blockchain / Web3"];
    return SKILLS_MAP["Technical"]; // Software / Web / Mobile default
  }
  if (bg.includes("Business")) return SKILLS_MAP["Business"];
  if (bg.includes("Research")) return SKILLS_MAP["Research"];
  if (bg.includes("Student")) return SKILLS_MAP["Student"];
  if (bg.includes("Creative")) return SKILLS_MAP["Creative"];
  if (bg.includes("Self Taught")) return SKILLS_MAP["Self Taught"];
  if (bg.includes("Just Have")) return SKILLS_MAP["Just Idea"];
  return SKILLS_MAP["Beginner"];
}
