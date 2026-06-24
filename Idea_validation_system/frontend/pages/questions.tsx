/** pages/questions.tsx — Step 3: Fixed + AI-generated follow-up questions */
import React, { useEffect, useRef, useState } from "react";
import { useRouter } from "next/router";
import Head from "next/head";
import { motion, AnimatePresence } from "framer-motion";
import Layout from "@/components/Layout";
import LoadingOverlay from "@/components/LoadingOverlay";
import ChatBubble from "@/components/ChatBubble";
import { useStore } from "@/lib/store";
import { getNextQuestion } from "@/lib/api";

// ── Fixed questions (always shown first, no API call needed) ─────────────────
const FIXED_QUESTIONS = [
  {
    text: "Have you built any version of this product yet — even a rough prototype, mockup, or demo?",
    yesPlaceholder: "Describe what you've built — what does it do, who has seen or used it?",
    noPlaceholder: "That's fine — what stage are you at right now? (idea only, planning, wireframes, etc.)",
  },
  {
    text: "Have you spoken with anyone who would actually use or pay for this — potential customers, users, or partners?",
    yesPlaceholder: "Who did you speak with? What did they say — was there strong interest or pushback?",
    noPlaceholder: "No problem — do you personally know anyone who experiences this problem?",
  },
  {
    text: "Do you have any paying customers, active pilot users, or signed letters of intent yet?",
    yesPlaceholder: "How many? What are they paying, or what have they committed to?",
    noPlaceholder: "Completely normal at this stage — what is your plan to get your first paying customer?",
  },
];

const TOTAL_QUESTIONS = 6; // 3 fixed + 3 AI
const AI_START = 3;

// ── AI question fallbacks in case the model fails ───────────────────────────
const AI_FALLBACKS = [
  "Who specifically are your first paying customers and why would they choose your solution over what they use today?",
  "How exactly will your product make money — what is the pricing model and how did you arrive at it?",
  "What makes this genuinely different from existing alternatives that someone could find today?",
];

export default function Questions() {
  const router = useRouter();
  const { state, dispatch } = useStore();
  const bottomRef = useRef<HTMLDivElement>(null);
  const fetchingForIdx = useRef<number | null>(null);

  const [answer, setAnswer] = useState("");
  const [yesNo, setYesNo] = useState<"yes" | "no" | null>(null);
  const [loadingQ, setLoadingQ] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!state.idea) router.replace("/");
  }, []);

  // Auto-scroll to bottom whenever history or loading state changes
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [state.answersHistory.length, loadingQ]);

  // Navigate to results when all 6 answers collected
  useEffect(() => {
    if (state.step === 4) router.push("/results");
  }, [state.step]);

  // Reset local inputs when question index changes
  useEffect(() => {
    setAnswer("");
    setYesNo(null);
    setError("");
  }, [state.currentQuestionIndex]);

  const idx = state.currentQuestionIndex;
  const isFixed = idx < AI_START;
  const aiIdx = idx - AI_START; // 0, 1, or 2 when in AI phase
  const currentAIQuestion: string | undefined = isFixed
    ? undefined
    : state.questions[aiIdx];

  // Fetch AI question when we enter the AI phase and the question isn't cached yet
  useEffect(() => {
    if (!state.idea || isFixed) return;
    if (state.questions.length <= aiIdx && fetchingForIdx.current !== idx) {
      fetchingForIdx.current = idx;
      setLoadingQ(true);
      // Pass only previous AI answers as history (not the 3 fixed ones)
      const aiHistory = state.answersHistory.slice(AI_START);
      getNextQuestion(
        state.idea,
        state.founderData.founder_name || "",
        state.founderData,
        aiHistory,
        state.searchContext || undefined,
      )
        .then((r) => dispatch({ type: "ADD_QUESTION", payload: r.question }))
        .catch(() => {
          dispatch({
            type: "ADD_QUESTION",
            payload: AI_FALLBACKS[aiIdx] ?? "What is your biggest challenge in making this idea real?",
          });
        })
        .finally(() => setLoadingQ(false));
    }
  }, [idx, state.questions.length, isFixed]);

  const handleSubmit = () => {
    if (isFixed) {
      if (!yesNo) { setError("Please select Yes or No first."); return; }
      const combined = yesNo === "yes"
        ? `Yes${answer.trim() ? ` — ${answer.trim()}` : ""}`
        : `No${answer.trim() ? ` — ${answer.trim()}` : ""}`;
      dispatch({
        type: "SAVE_QUESTION_ANSWER",
        question: FIXED_QUESTIONS[idx].text,
        answer: combined,
      });
    } else {
      if (!answer.trim()) { setError("Please type your answer or click I Don't Know."); return; }
      dispatch({
        type: "SAVE_QUESTION_ANSWER",
        question: currentAIQuestion!,
        answer: answer.trim(),
      });
    }
    setError("");
  };

  const isLastQuestion = idx === TOTAL_QUESTIONS - 1;
  const currentFixedQ = isFixed ? FIXED_QUESTIONS[idx] : null;
  const activePlaceholder = currentFixedQ
    ? (yesNo === "yes" ? currentFixedQ.yesPlaceholder : yesNo === "no" ? currentFixedQ.noPlaceholder : "Select Yes or No above first…")
    : "Type your answer here — be as detailed as you like…";

  return (
    <>
      <Head>
        <title>Idea Questions — ThynxAI Idea Lab</title>
      </Head>

      <Layout>
        <div className="page-header">
          <div className="page-header__tag">Step 3 of 4</div>
          <h1 className="page-header__title">Let's Dig Deeper</h1>
          <p className="page-header__sub">
            6 questions to power your full analysis — your answers shape how honest the report is.
          </p>
        </div>

        {/* Progress dots */}
        <div className="question-progress" style={{ marginBottom: "1.5rem" }}>
          {Array.from({ length: TOTAL_QUESTIONS }).map((_, i) => (
            <div
              key={i}
              className={`question-progress__dot ${
                i < idx ? "question-progress__dot--done" :
                i === idx ? "question-progress__dot--active" : ""
              }`}
            />
          ))}
        </div>

        {/* Previous Q&A history — always visible */}
        <div className="chat-history">
          {state.answersHistory.map((item, i) => (
            <React.Fragment key={i}>
              <ChatBubble role="ai" message={item.question} animate={false} />
              <ChatBubble role="user" message={item.answer} animate={false} />
            </React.Fragment>
          ))}

          {/* Current question bubble */}
          {isFixed && currentFixedQ && (
            <ChatBubble role="ai" message={currentFixedQ.text} />
          )}
          {!isFixed && loadingQ && (
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", padding: "0.75rem", color: "var(--text-muted)" }}>
              <div className="loading-spinner" style={{ width: 24, height: 24, borderWidth: 2 }} />
              <span>AI is generating the next question…</span>
            </div>
          )}
          {!isFixed && !loadingQ && currentAIQuestion && (
            <ChatBubble role="ai" message={currentAIQuestion} />
          )}
        </div>
        <div ref={bottomRef} />

        {/* Answer input area */}
        <AnimatePresence mode="wait">
          {(isFixed || (!loadingQ && currentAIQuestion)) && (
            <motion.div
              key={idx}
              className="card"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.22 }}
            >
              {/* Fixed questions: Yes/No toggle first */}
              {isFixed && (
                <div style={{ display: "flex", gap: "0.75rem", marginBottom: "1rem" }}>
                  <button
                    className={`btn ${yesNo === "yes" ? "btn--primary" : "btn--ghost"}`}
                    style={{ flex: 1 }}
                    onClick={() => { setYesNo("yes"); setError(""); }}
                  >
                    ✅ Yes
                  </button>
                  <button
                    className={`btn ${yesNo === "no" ? "btn--primary" : "btn--ghost"}`}
                    style={{ flex: 1 }}
                    onClick={() => { setYesNo("no"); setError(""); }}
                  >
                    ❌ Not Yet
                  </button>
                </div>
              )}

              {/* Text input — always shown, placeholder changes based on yes/no */}
              <p className="text-muted" style={{ marginBottom: "0.5rem", fontSize: "0.82rem" }}>
                {isFixed
                  ? "Optional — add details to make the analysis more accurate:"
                  : "There are no wrong answers — be as honest and detailed as you can:"}
              </p>
              <textarea
                className="form-textarea"
                value={answer}
                onChange={(e) => { setAnswer(e.target.value); setError(""); }}
                placeholder={activePlaceholder}
                rows={4}
                style={{ marginBottom: "1rem" }}
                disabled={isFixed && !yesNo}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleSubmit();
                }}
                autoFocus={!isFixed}
              />

              <AnimatePresence>
                {error && (
                  <motion.div
                    className="alert alert--error"
                    style={{ marginBottom: "0.75rem" }}
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                  >
                    ⚠️ {error}
                  </motion.div>
                )}
              </AnimatePresence>

              <div className="btn-group">
                {!isFixed && (
                  <button
                    className="btn btn--ghost"
                    onClick={() => {
                      setAnswer("I don't know");
                      dispatch({
                        type: "SAVE_QUESTION_ANSWER",
                        question: currentAIQuestion!,
                        answer: "I don't know",
                      });
                    }}
                  >
                    🤷 I Don't Know
                  </button>
                )}
                <button
                  className="btn btn--primary"
                  onClick={handleSubmit}
                  style={{ marginLeft: "auto" }}
                  disabled={isFixed ? !yesNo : false}
                >
                  {isLastQuestion ? "🚀 Analyse My Idea" : "Next →"}
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </Layout>
    </>
  );
}
