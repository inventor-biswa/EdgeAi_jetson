/** pages/questions.tsx — Step 3: Adaptive AI Questions */
import React, { useEffect, useRef, useState } from "react";
import { useRouter } from "next/router";
import Head from "next/head";
import { motion, AnimatePresence } from "framer-motion";
import Layout from "@/components/Layout";
import LoadingOverlay from "@/components/LoadingOverlay";
import ChatBubble from "@/components/ChatBubble";
import { useStore } from "@/lib/store";
import { getNextQuestion } from "@/lib/api";

const TOTAL_QUESTIONS = 4;

export default function Questions() {
  const router = useRouter();
  const { state, dispatch } = useStore();
  const [answer, setAnswer] = useState("");
  const [loadingQ, setLoadingQ] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const fetchingForIdx = useRef<number | null>(null);

  useEffect(() => {
    if (!state.idea) { router.replace("/"); return; }
  }, []);

  const idx = state.currentQuestionIndex;
  const currentQuestion: string | undefined = state.questions[idx];

  // Fetch next question if not yet generated
  useEffect(() => {
    if (!state.idea) return;
    if (state.questions.length <= idx && fetchingForIdx.current !== idx) {
      fetchingForIdx.current = idx;
      setLoadingQ(true);
      getNextQuestion(
        state.idea,
        state.founderData.founder_name || "",
        state.founderData,
        state.answersHistory,
        state.searchContext || undefined,
      )
        .then((r) => {
          dispatch({ type: "ADD_QUESTION", payload: r.question });
        })
        .catch(() => {
          const fallbacks = [
            "What problem does your idea solve for your first customer?",
            "How would someone find out about your product for the first time?",
            "What is the one thing that makes your idea different from others?",
            "If you had to launch in one month, what would you build first?",
          ];
          dispatch({
            type: "ADD_QUESTION",
            payload: fallbacks[idx] || "What is your biggest challenge in building this?",
          });
        })
        .finally(() => setLoadingQ(false));
    }
  }, [idx, state.questions.length]);

  // Auto-navigate when step changes to 4
  useEffect(() => {
    if (state.step === 4) {
      router.push("/results");
    }
  }, [state.step]);

  const handleSubmit = (ans: string) => {
    if (!ans.trim()) { setError("Please type your answer or click I Don't Know."); return; }
    setError("");
    dispatch({ type: "SAVE_QUESTION_ANSWER", question: currentQuestion!, answer: ans });
    setAnswer("");
  };

  const isLast = idx === TOTAL_QUESTIONS - 1;

  return (
    <>
      <Head>
        <title>Idea Questions — ThynxAI Idea Lab</title>
      </Head>

      <AnimatePresence>
        {submitting && <LoadingOverlay message="Analyzing your idea — this takes a minute…" />}
      </AnimatePresence>

      <Layout>
        <div className="page-header">
          <div className="page-header__tag">Step 3 of 4</div>
          <h1 className="page-header__title">Let's Dig Deeper</h1>
          <p className="page-header__sub">
            4 personalised questions to power your full analysis.
          </p>
        </div>

        {/* Progress dots */}
        <div className="question-progress">
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

        {/* Previous Q&A history */}
        <div className="chat-history">
          {state.answersHistory.map((item, i) => (
            <React.Fragment key={i}>
              <ChatBubble role="ai" message={item.question} animate={false} />
              <ChatBubble role="user" message={item.answer} animate={false} />
            </React.Fragment>
          ))}

          {/* Current question */}
          {loadingQ ? (
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", padding: "0.75rem", color: "var(--text-muted)" }}>
              <div className="loading-spinner" style={{ width: 24, height: 24, borderWidth: 2 }} />
              <span>AI is formulating the next question…</span>
            </div>
          ) : currentQuestion ? (
            <ChatBubble role="ai" message={currentQuestion} />
          ) : null}
        </div>

        {/* Answer input */}
        <AnimatePresence mode="wait">
          {currentQuestion && !loadingQ && (
            <motion.div
              key={idx}
              className="card"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
            >
              <p className="text-muted" style={{ marginBottom: "0.75rem" }}>
                There are no wrong answers — be as honest as you can.
              </p>

              <textarea
                className="form-textarea"
                value={answer}
                onChange={(e) => { setAnswer(e.target.value); setError(""); }}
                placeholder="Type your answer here…"
                rows={4}
                style={{ marginBottom: "1rem" }}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleSubmit(answer);
                }}
                autoFocus
              />

              <AnimatePresence>
                {error && (
                  <motion.div className="alert alert--error" style={{ marginBottom: "0.75rem" }}
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                    ⚠️ {error}
                  </motion.div>
                )}
              </AnimatePresence>

              <div className="btn-group">
                <button
                  className="btn btn--ghost"
                  onClick={() => handleSubmit("I don't know")}
                >
                  🤷 I Don't Know
                </button>
                <button
                  className="btn btn--primary"
                  onClick={() => handleSubmit(answer)}
                  style={{ marginLeft: "auto" }}
                  disabled={submitting}
                >
                  {isLast ? "🚀 Analyse My Idea" : "Next →"}
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </Layout>
    </>
  );
}
