/**
 * pages/profile.tsx — Step 2: Founder Profile Chat
 * Renders the 16+ question chat flow from app.py Step 2,
 * now as a beautiful chat interface.
 */
import React, { useEffect, useRef, useState } from "react";
import { useRouter } from "next/router";
import Head from "next/head";
import { motion, AnimatePresence } from "framer-motion";
import Layout from "@/components/Layout";
import ChatBubble from "@/components/ChatBubble";
import LoadingOverlay from "@/components/LoadingOverlay";
import { useStore } from "@/lib/store";
import { runSearch } from "@/lib/api";
import {
  getActiveQuestions,
  getSkillsForBackground,
  Question,
} from "@/lib/founderQuestions";

const COUNTRIES = ["India", "USA", "UK", "UAE", "Other"];

export default function Profile() {
  const router = useRouter();
  const { state, dispatch } = useStore();
  const bottomRef = useRef<HTMLDivElement>(null);
  const [localAnswer, setLocalAnswer] = useState("");
  const [selectedCountry, setSelectedCountry] = useState("India");
  const [city, setCity] = useState("");
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [searching, setSearching] = useState(false);

  // Guard — redirect to home if no idea
  useEffect(() => {
    if (!state.idea) router.replace("/");
  }, [state.idea, router]);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [state.chatHistory]);

  // Reset local inputs when question changes
  useEffect(() => {
    setLocalAnswer("");
    setSelectedCountry("India");
    setCity("");
    setSelectedSkills([]);
    setError("");
  }, [state.chatIndex]);

  const activeQuestions = getActiveQuestions(state.founderData);
  const currentQ: Question | undefined = activeQuestions[state.chatIndex];

  const saveAnswer = (key: string, answer: string, question: string) => {
    if (!answer.trim()) return;
    dispatch({ type: "SAVE_FOUNDER_ANSWER", key, answer: answer.trim(), question });
  };

  const handleNext = async () => {
    setError("");
    if (!currentQ) return;

    if (currentQ.key === "location") {
      if (!city.trim() || city.trim().length < 2) {
        setError("Please enter a valid city name."); return;
      }
      saveAnswer("location", `${city.trim()}, ${selectedCountry}`, currentQ.label);
      return;
    }

    if (currentQ.type === "checkbox") {
      if (selectedSkills.length === 0) {
        setError("Please select at least one skill or click Skip."); return;
      }
      saveAnswer("skills", selectedSkills.join(", "), currentQ.label);
      return;
    }

    if (!localAnswer.trim()) { setError("Please answer this question."); return; }
    saveAnswer(currentQ.key, localAnswer, currentQ.label);
  };

  const handleSkip = () => {
    if (!currentQ?.allowSkip) return;
    saveAnswer(currentQ.key, currentQ.skipValue || "Skipped", currentQ.label);
  };

  const handleBack = () => {
    if (state.chatIndex === 0) { router.push("/"); return; }
    dispatch({ type: "GO_BACK_CHAT" });
  };

  // All questions answered — run search then go to step 3
  useEffect(() => {
    if (currentQ === undefined && state.chatHistory.length > 0 && !searching) {
      (async () => {
        setSearching(true);
        try {
          const result = await runSearch(state.idea, state.founderData);
          dispatch({ type: "SET_SEARCH_CONTEXT", payload: result.search_context });
        } catch {}
        dispatch({ type: "SET_STEP", payload: 3 });
        router.push("/questions");
      })();
    }
  }, [currentQ, state.chatHistory.length]);

  const skillOptions = getSkillsForBackground(state.founderData.background || "");

  const toggleSkill = (skill: string) => {
    setSelectedSkills((prev) =>
      prev.includes(skill) ? prev.filter((s) => s !== skill) : [...prev, skill]
    );
  };

  if (!state.idea) return null;

  return (
    <>
      <Head>
        <title>Founder Profile — ThynxAI Idea Lab</title>
      </Head>

      <AnimatePresence>
        {searching && <LoadingOverlay message="Researching the market for your idea…" />}
      </AnimatePresence>

      <Layout>
        <div className="page-header">
          <div className="page-header__tag">Step 2 of 4</div>
          <h1 className="page-header__title">Tell Us About Yourself</h1>
          <p className="page-header__sub">
            Answer a few questions so our AI can personalise your analysis.
          </p>
        </div>

        {/* Progress bar */}
        {activeQuestions.length > 0 && (
          <div style={{ marginBottom: "1.5rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "0.4rem" }}>
              <span>Question {Math.min(state.chatIndex + 1, activeQuestions.length)} of {activeQuestions.length}</span>
              <span>{Math.round((state.chatIndex / activeQuestions.length) * 100)}% done</span>
            </div>
            <div style={{ height: "4px", borderRadius: "999px", background: "var(--glass-border)", overflow: "hidden" }}>
              <motion.div
                style={{ height: "100%", background: "var(--thynx-blue)", borderRadius: "999px" }}
                initial={{ width: 0 }}
                animate={{ width: `${(state.chatIndex / activeQuestions.length) * 100}%` }}
                transition={{ duration: 0.4 }}
              />
            </div>
          </div>
        )}

        {/* Chat history */}
        <div className="chat-history">
          {state.chatHistory.map((item, i) => (
            <React.Fragment key={i}>
              <ChatBubble role="ai" message={item.question} animate={false} />
              <ChatBubble role="user" message={item.answer} animate={false} />
            </React.Fragment>
          ))}

          {/* Current question */}
          {currentQ && (
            <ChatBubble role="ai" message={currentQ.label} />
          )}

          {currentQ?.caption && (
            <p className="text-muted" style={{ paddingLeft: "0.5rem" }}>
              {currentQ.caption}
            </p>
          )}
        </div>
        <div ref={bottomRef} />

        {/* Input area */}
        <AnimatePresence mode="wait">
          {currentQ && (
            <motion.div
              key={state.chatIndex}
              className="card"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.22 }}
            >
              {/* Location — two inputs */}
              {currentQ.key === "location" ? (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", marginBottom: "1rem" }}>
                  <div>
                    <label className="form-label">Country</label>
                    <select
                      className="form-select"
                      value={selectedCountry}
                      onChange={(e) => setSelectedCountry(e.target.value)}
                    >
                      {COUNTRIES.map((c) => <option key={c}>{c}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="form-label">City</label>
                    <input
                      className="form-input"
                      value={city}
                      onChange={(e) => { setCity(e.target.value); setError(""); }}
                      placeholder="e.g. Bhubaneswar"
                      onKeyDown={(e) => e.key === "Enter" && handleNext()}
                    />
                  </div>
                </div>
              ) : currentQ.type === "checkbox" ? (
                <div>
                  <div className="checkbox-grid" style={{ marginBottom: "1rem" }}>
                    {skillOptions.map((skill) => (
                      <div
                        key={skill}
                        className={`checkbox-item ${selectedSkills.includes(skill) ? "checkbox-item--checked" : ""}`}
                        onClick={() => { toggleSkill(skill); setError(""); }}
                      >
                        <input type="checkbox" readOnly checked={selectedSkills.includes(skill)} />
                        <div className="checkbox-box">
                          {selectedSkills.includes(skill) && (
                            <svg width="10" height="10" viewBox="0 0 10 10">
                              <path d="M2 5l2.5 2.5L8 3" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" fill="none" />
                            </svg>
                          )}
                        </div>
                        <span>{skill}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : currentQ.type === "select" ? (
                <select
                  className="form-select"
                  value={localAnswer}
                  onChange={(e) => { setLocalAnswer(e.target.value); setError(""); }}
                  style={{ marginBottom: "1rem" }}
                >
                  <option value="">— Select an option —</option>
                  {(currentQ.options || []).map((opt) => (
                    <option key={opt} value={opt}>{opt}</option>
                  ))}
                </select>
              ) : (
                <textarea
                  className="form-textarea"
                  value={localAnswer}
                  onChange={(e) => { setLocalAnswer(e.target.value); setError(""); }}
                  placeholder={currentQ.placeholder}
                  rows={3}
                  style={{ marginBottom: "1rem" }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleNext();
                  }}
                />
              )}

              <AnimatePresence>
                {error && (
                  <motion.div className="alert alert--error" style={{ marginBottom: "0.75rem" }}
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                    ⚠️ {error}
                  </motion.div>
                )}
              </AnimatePresence>

              <div className="btn-group">
                <button className="btn btn--ghost" onClick={handleBack}>← Back</button>
                {currentQ.allowSkip && (
                  <button className="btn btn--ghost" onClick={handleSkip}>Skip →</button>
                )}
                <button className="btn btn--primary" onClick={handleNext} style={{ marginLeft: "auto" }}>
                  {state.chatIndex === activeQuestions.length - 1 ? "Finish Profile →" : "Next →"}
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </Layout>
    </>
  );
}
