/** pages/index.tsx — Step 1: Idea Input + History Panel */
import React, { useState, useEffect } from "react";
import { useRouter } from "next/router";
import Head from "next/head";
import { motion, AnimatePresence } from "framer-motion";
import Layout from "@/components/Layout";
import LoadingOverlay from "@/components/LoadingOverlay";
import ThynxLogo from "@/components/ThynxLogo";
import { useStore } from "@/lib/store";
import { validateIdea, getAnalyses, getAnalysis, deleteAnalysis, AnalysisSummary } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const { state, dispatch } = useStore();
  const [idea, setIdea] = useState(state.idea || "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState<AnalysisSummary[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => { setMounted(true); }, []);

  // Load history on mount
  useEffect(() => {
    getAnalyses()
      .then(setHistory)
      .catch(() => setHistory([]))
      .finally(() => setHistoryLoading(false));
  }, []);

  const handleSubmit = async () => {
    setError("");
    if (!idea.trim()) { setError("Please describe your startup idea first."); return; }
    setLoading(true);
    try {
      const result = await validateIdea(idea.trim());
      if (result.status === "INVALID") {
        setError(result.reason || "That doesn't seem like a startup idea. Please be more specific.");
        setLoading(false);
        return;
      }
      dispatch({ type: "START_NEW_IDEA", payload: idea.trim() });
      router.push("/profile");
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Could not reach the AI server. Is the backend running?");
      setLoading(false);
    }
  };

  const handleViewHistory = async (id: number) => {
    try {
      const full = await getAnalysis(id);
      dispatch({ type: "LOAD_SAVED_ANALYSIS", payload: full });
      router.push("/results");
    } catch {
      setError("Could not load this analysis.");
    }
  };

  const handleDelete = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    setDeletingId(id);
    try {
      await deleteAnalysis(id);
      setHistory((prev) => prev.filter((h) => h.id !== id));
    } catch {
      setError("Could not delete analysis.");
    }
    setDeletingId(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleSubmit();
  };

  const scoreColor = (s: string) => {
    const n = parseInt(s);
    if (n >= 7) return "#a6e3a1";
    if (n >= 5) return "#f9e2af";
    return "#f38ba8";
  };

  return (
    <>
      <Head>
        <title>ThynxAI Idea Lab — AI-Powered Startup Validator</title>
        <meta name="description" content="Validate your startup idea with AI. Get a full 8-dimension analysis, market insights, and pitch deck — all running offline on NVIDIA Jetson." />
      </Head>

      <AnimatePresence>{loading && <LoadingOverlay message="Validating your idea…" />}</AnimatePresence>

      <Layout>
        {!mounted ? null : (<>
        {/* Hero */}
        <motion.div
          className="hero"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="hero__logo">
            <ThynxLogo size="lg" />
          </div>
          <h1 className="hero__title">Idea Lab</h1>
          <p className="hero__sub">
            AI-powered startup idea validator — running fully offline on NVIDIA Jetson Orin Nano.
          </p>
        </motion.div>

        {/* Feature badges */}
        <motion.div
          style={{ display: "flex", justifyContent: "center", gap: "0.75rem", flexWrap: "wrap", marginBottom: "2.5rem" }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.25 }}
        >
          {["🧠 8-Dimension Analysis", "📊 Market Research", "🎯 Pitch Deck", "⚡ 100% Offline"].map((tag) => (
            <span key={tag} className="page-header__tag">{tag}</span>
          ))}
        </motion.div>

        {/* Input card */}
        <motion.div
          className="card card--blue"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <div style={{ marginBottom: "1.25rem" }}>
            <div className="page-header__tag" style={{ marginBottom: "0.75rem" }}>Step 1 of 4</div>
            <h2 style={{ fontSize: "1.4rem", fontWeight: 700, marginBottom: "0.5rem" }}>
              Describe Your Startup Idea
            </h2>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.92rem" }}>
              The more detail you give, the richer your analysis will be. Aim for 2–3 sentences.
            </p>
          </div>

          <textarea
            className="form-textarea"
            value={idea}
            onChange={(e) => { setIdea(e.target.value); setError(""); }}
            onKeyDown={handleKeyDown}
            placeholder="e.g. An AI-powered app that helps restaurants predict food waste using past order data and weather patterns, reducing waste by 30% and saving costs…"
            rows={5}
            style={{ marginBottom: "1.25rem" }}
          />

          <AnimatePresence>
            {error && (
              <motion.div
                className="alert alert--error"
                style={{ marginBottom: "1rem" }}
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
              >
                ⚠️ {error}
              </motion.div>
            )}
          </AnimatePresence>

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span className="text-muted">⌘ + Enter to submit</span>
            <button
              className="btn btn--primary"
              onClick={handleSubmit}
              disabled={loading}
              style={{ minWidth: 160 }}
            >
              Validate Idea →
            </button>
          </div>
        </motion.div>

        {/* ── Previous Analyses History ─────────────────────────────────── */}
        <motion.div
          style={{ marginTop: "3rem" }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
        >
          <h3 style={{
            fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.1em",
            color: "var(--text-muted)", marginBottom: "1rem",
            display: "flex", alignItems: "center", gap: "0.5rem",
          }}>
            🕐 Previous Analyses
            <span style={{ fontSize: "0.75rem", opacity: 0.6 }}>
              ({historyLoading ? "…" : history.length} saved)
            </span>
          </h3>

          {historyLoading ? (
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "var(--text-muted)", fontSize: "0.85rem" }}>
              <div className="loading-spinner" style={{ width: 18, height: 18, borderWidth: 2 }} />
              Loading history…
            </div>
          ) : history.length === 0 ? (
            <div className="card" style={{ textAlign: "center", padding: "2rem", color: "var(--text-muted)", fontSize: "0.88rem" }}>
              No saved analyses yet. Run your first validation above!
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              {history.map((h) => (
                <motion.div
                  key={h.id}
                  className="card"
                  whileHover={{ y: -2, boxShadow: "0 6px 24px rgba(100,120,255,0.15)" }}
                  style={{ cursor: "pointer", display: "grid", gridTemplateColumns: "1fr auto", gap: "1rem", alignItems: "center" }}
                  onClick={() => handleViewHistory(h.id)}
                >
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", marginBottom: "0.3rem" }}>
                      <span style={{
                        fontWeight: 700, fontSize: "1rem",
                        color: scoreColor(h.score),
                        background: "rgba(255,255,255,0.06)",
                        padding: "0.15rem 0.5rem", borderRadius: "6px", letterSpacing: "0.02em",
                      }}>
                        {h.score}/10
                      </span>
                      <span style={{ fontWeight: 600, fontSize: "0.92rem", color: "var(--text-primary)" }}>
                        {h.founder_name}
                      </span>
                    </div>
                    <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", margin: 0, lineHeight: 1.4 }}>
                      {h.idea_summary}
                    </p>
                    <p style={{ color: "var(--text-muted)", fontSize: "0.75rem", marginTop: "0.3rem" }}>
                      {new Date(h.saved_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" })}
                    </p>
                  </div>
                  <div style={{ display: "flex", gap: "0.5rem", flexShrink: 0 }}>
                    <button
                      className="btn btn--ghost"
                      style={{ padding: "0.4rem 0.8rem", fontSize: "0.82rem" }}
                      onClick={(e) => { e.stopPropagation(); handleViewHistory(h.id); }}
                    >
                      View Report →
                    </button>
                    <button
                      className="btn btn--danger"
                      style={{ padding: "0.4rem 0.7rem", fontSize: "0.82rem" }}
                      onClick={(e) => handleDelete(e, h.id)}
                      disabled={deletingId === h.id}
                      title="Delete this analysis"
                    >
                      {deletingId === h.id ? "…" : "🗑"}
                    </button>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </motion.div>

        {/* How it works */}
        <motion.div
          style={{ marginTop: "3rem" }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          <h3 style={{ textAlign: "center", fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--text-muted)", marginBottom: "1.5rem" }}>
            How It Works
          </h3>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "1rem" }}>
            {[
              { n: "01", t: "Describe Idea",       d: "Tell us about your startup concept" },
              { n: "02", t: "Build Your Profile",  d: "Share your background & experience" },
              { n: "03", t: "Answer Questions",    d: "4 AI-generated follow-up questions" },
              { n: "04", t: "Get Full Analysis",   d: "Scores, insights & pitch deck ready" },
            ].map(({ n, t, d }) => (
              <div key={n} className="card" style={{ padding: "1.25rem", textAlign: "center" }}>
                <div style={{ fontSize: "1.6rem", fontWeight: 900, fontFamily: "'Space Grotesk',sans-serif", color: "var(--thynx-blue-light)", opacity: 0.5, marginBottom: "0.5rem" }}>{n}</div>
                <div style={{ fontWeight: 700, marginBottom: "0.3rem" }}>{t}</div>
                <div style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>{d}</div>
              </div>
            ))}
          </div>
        </motion.div>
        </>)}
      </Layout>
    </>
  );
}
