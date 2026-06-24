/** pages/results.tsx — Step 4: Full Analysis Dashboard */
import React, { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Head from "next/head";
import { motion, AnimatePresence } from "framer-motion";
import Layout from "@/components/Layout";
import LoadingOverlay from "@/components/LoadingOverlay";
import ScoreCard from "@/components/ScoreCard";
import AnalysisSection from "@/components/AnalysisSection";
import { useStore } from "@/lib/store";
import {
  analyzeIdea,
  downloadJSON,
  downloadMarkdown,
  downloadPPT,
  triggerDownload,
  sendFollowup,
  ChatMessage,
} from "@/lib/api";

function isYes(val: string) { return /yes/i.test(val); }
function isNo(val:  string) { return /no/i.test(val); }

function ReadinessChip({ label, value }: { label: string; value: string }) {
  const cls = isYes(value) ? "status-badge--yes" : isNo(value) ? "status-badge--no" : "status-badge--warn";
  const icon = isYes(value) ? "✅" : isNo(value) ? "❌" : "⚠️";
  return (
    <div className="readiness-item">
      <div className="readiness-item__label">{label}</div>
      <div className={`status-badge ${cls}`} style={{ fontSize: "0.78rem" }}>
        {icon} {value}
      </div>
    </div>
  );
}

export default function Results() {
  const router = useRouter();
  const { state, dispatch } = useStore();
  const [loading, setLoading] = useState(false);
  const [loadMsg, setLoadMsg] = useState("Analyzing your idea…");
  const [dlLoading, setDlLoading] = useState<string | null>(null);
  const [pptReady, setPptReady] = useState(false);
  const [error, setError] = useState("");
  const [followupMessages, setFollowupMessages] = useState<ChatMessage[]>([]);
  const [followupInput, setFollowupInput] = useState("");
  const [followupLoading, setFollowupLoading] = useState(false);

  useEffect(() => {
    if (!state.idea) { router.replace("/"); return; }
  }, []);

  // Run analysis if not yet done
  useEffect(() => {
    if (!state.idea || state.analysis) return;
    if (state.followupQA.length === 0) return;

    setLoading(true);
    setLoadMsg("Running 8-dimension analysis — this may take a minute…");

    analyzeIdea({
      idea: state.idea,
      founder_name: state.founderData.founder_name || "",
      founder_data: state.founderData,
      followup_qa: state.followupQA,
      search_context: state.searchContext || undefined,
    })
      .then((analysis) => {
        dispatch({ type: "SET_ANALYSIS", payload: analysis });
        dispatch({ type: "SET_STEP", payload: 4 });
      })
      .catch((e) => {
        setError(e?.response?.data?.detail || "Analysis failed. Please try again.");
      })
      .finally(() => setLoading(false));
  }, [state.idea, state.analysis, state.followupQA]);

  const handleDownload = async (type: "json" | "md" | "ppt") => {
    if (!state.analysis) return;
    setDlLoading(type);
    try {
      if (type === "json") {
        const blob = await downloadJSON(state.analysis);
        triggerDownload(blob, "thynxai_analysis.json");
      } else if (type === "md") {
        const blob = await downloadMarkdown(state.analysis);
        triggerDownload(blob, "thynxai_report.md");
      } else {
        setLoadMsg("Building your pitch deck…");
        setLoading(true);
        const blob = await downloadPPT(state.analysis);
        triggerDownload(blob, "thynxai_pitch_deck.pptx");
        setPptReady(true);
        setLoading(false);
      }
    } catch (e: any) {
      setError("Download failed: " + (e?.message || "unknown error"));
    }
    setDlLoading(null);
  };

  const sendFollowupMsg = async () => {
    const text = followupInput.trim();
    if (!text || followupLoading || !analysis) return;
    const userMsg: ChatMessage = { role: "user", content: text };
    setFollowupMessages((prev) => [...prev, userMsg]);
    setFollowupInput("");
    setFollowupLoading(true);
    try {
      const reply = await sendFollowup(analysis, text, [...followupMessages, userMsg]);
      setFollowupMessages((prev) => [...prev, { role: "assistant", content: reply }]);
    } catch {
      setFollowupMessages((prev) => [
        ...prev,
        { role: "assistant", content: "⚠️ Could not get a response. Please try again." },
      ]);
    }
    setFollowupLoading(false);
  };

  const handleReset = () => {
    dispatch({ type: "RESET" });
    router.push("/");
  };

  const analysis = state.analysis;

  return (
    <>
      <Head>
        <title>Analysis Results — ThynxAI Idea Lab</title>
      </Head>

      <AnimatePresence>
        {loading && <LoadingOverlay message={loadMsg} />}
      </AnimatePresence>

      <Layout wide>
        {error && (
          <div className="alert alert--error" style={{ marginBottom: "1.5rem" }}>
            ⚠️ {error}
            <button className="btn btn--ghost" onClick={handleReset} style={{ marginLeft: "auto" }}>
              Start Over
            </button>
          </div>
        )}

        {analysis && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            {/* ── Header ─────────────────────────────────────────────── */}
            <div className="page-header">
              <div className="page-header__tag">Step 4 of 4 · Analysis Complete</div>
              <h1 className="page-header__title">Your Startup Report</h1>
              <p className="page-header__sub">
                {analysis.founder_name && `Prepared for ${analysis.founder_name} · `}
                {analysis.idea_summary}
              </p>
            </div>

            {/* ── Overall Score + Readiness ───────────────────────────── */}
            <motion.div
              className="card card--blue"
              style={{ marginBottom: "1.5rem" }}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
            >
              <div style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "2rem", alignItems: "start" }}>
                <div className="overall-ring">
                  <div className="overall-ring__score">
                    {analysis.overall?.score ?? "—"}<span style={{ fontSize: "2rem", opacity: 0.5 }}>/10</span>
                  </div>
                  <div className="overall-ring__label">Overall Score</div>
                </div>
                <div>
                  <h2 style={{ fontSize: "1.15rem", fontWeight: 700, marginBottom: "0.5rem" }}>
                    Readiness Summary
                  </h2>
                  <div className="readiness-grid">
                    <ReadinessChip label="MVP Ready"        value={analysis.overall?.is_mvp_ready || "N/A"} />
                    <ReadinessChip label="Investment Ready"  value={analysis.overall?.is_investment_ready || "N/A"} />
                    <ReadinessChip label="Incubator Ready"   value={analysis.overall?.is_incubator_ready || "N/A"} />
                  </div>
                  {analysis.overall?.final_verdict && (
                    <div className="alert alert--info" style={{ marginTop: "1rem", fontSize: "0.88rem" }}>
                      💡 {analysis.overall.final_verdict}
                    </div>
                  )}
                </div>
              </div>

              {/* Readiness action buttons */}
              <div className="btn-group" style={{ marginTop: "1.25rem", borderTop: "1px solid var(--glass-border)", paddingTop: "1.25rem" }}>
                {isNo(analysis.overall?.is_mvp_ready || "") && (
                  <button className="btn btn--ghost" onClick={() => router.push("/mvp-help")}>
                    🔧 How to become MVP Ready →
                  </button>
                )}
                {isNo(analysis.overall?.is_investment_ready || "") && (
                  <button className="btn btn--ghost" onClick={() => router.push("/investment-help")}>
                    💰 How to become Investment Ready →
                  </button>
                )}
              </div>
            </motion.div>

            {/* ── Scores ─────────────────────────────────────────────── */}
            <h2 style={{ fontWeight: 700, marginBottom: "1rem" }}>📊 Dimension Scores</h2>
            <div className="scores-grid" style={{ marginBottom: "2rem" }}>
              {Object.entries(analysis.scores || {}).map(([key, val]) => (
                <ScoreCard
                  key={key}
                  name={key}
                  score={parseInt(String(val.score)) || 0}
                  reasoning={val.reasoning}
                />
              ))}
            </div>

            {/* ── Collapsible sections ────────────────────────────────── */}
            <AnalysisSection icon="🎯" title="Problem Statement" defaultOpen>
              {(() => {
                const p = analysis.problem_statement || {};
                return (
                  <>
                    <div className="info-row"><div className="info-row__label">Description</div><div className="info-row__value">{p.description}</div></div>
                    <div className="info-row"><div className="info-row__label">Target Audience</div><div className="info-row__value">{p.target_audience}</div></div>
                    <div className="info-row"><div className="info-row__label">Why Current Solutions Fail</div><div className="info-row__value">{p.why_current_solutions_fail}</div></div>
                    <div className="info-row"><div className="info-row__label">Who Suffers Most</div><div className="info-row__value">{p.who_suffers_most}</div></div>
                    <div className="info-row"><div className="info-row__label">Market Size Hint</div><div className="info-row__value">{p.market_size_hint}</div></div>
                    <div className="info-row"><div className="info-row__label">Current Workarounds</div><div className="info-row__value">{p.current_workarounds}</div></div>
                    {p.real_world_example && (
                      <div className="alert alert--info" style={{ marginTop: "0.75rem" }}>
                        📖 {p.real_world_example}
                      </div>
                    )}
                    {p.pain_points?.length > 0 && (
                      <ul className="bullet-list" style={{ marginTop: "0.75rem" }}>
                        {p.pain_points.map((pt: string, i: number) => <li key={i}>{pt}</li>)}
                      </ul>
                    )}
                  </>
                );
              })()}
            </AnalysisSection>

            <AnalysisSection icon="💡" title="Proposed Solution">
              {(() => {
                const s = analysis.proposed_solution || {};
                return (
                  <>
                    {s.one_line_pitch && (
                      <div className="alert alert--info" style={{ marginBottom: "1rem", fontWeight: 600 }}>
                        🎯 {s.one_line_pitch}
                      </div>
                    )}
                    <div className="info-row"><div className="info-row__label">Simple Explanation</div><div className="info-row__value">{s.simple_explanation}</div></div>
                    <div className="info-row"><div className="info-row__label">Unfair Advantage</div><div className="info-row__value">{s.unfair_advantage}</div></div>
                    {s.step_by_step_how_it_works?.length > 0 && (
                      <>
                        <p style={{ fontWeight: 600, marginTop: "0.75rem", marginBottom: "0.4rem", fontSize: "0.85rem", color: "var(--text-secondary)" }}>HOW IT WORKS</p>
                        <ol style={{ paddingLeft: "1.25rem", display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                          {s.step_by_step_how_it_works.map((step: string, i: number) => (
                            <li key={i} style={{ fontSize: "0.92rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>{step}</li>
                          ))}
                        </ol>
                      </>
                    )}
                    {s.key_features?.length > 0 && (
                      <>
                        <p style={{ fontWeight: 600, marginTop: "0.75rem", marginBottom: "0.4rem", fontSize: "0.85rem", color: "var(--text-secondary)" }}>KEY FEATURES</p>
                        <ul className="bullet-list">
                          {s.key_features.map((f: string, i: number) => <li key={i}>{f}</li>)}
                        </ul>
                      </>
                    )}
                  </>
                );
              })()}
            </AnalysisSection>

            <AnalysisSection icon="🔬" title="Core Innovation">
              {(() => {
                const c = analysis.core_innovation || {};
                return (
                  <>
                    <div className="info-row"><div className="info-row__label">Uniqueness</div><div className="info-row__value">{c.uniqueness}</div></div>
                    <div className="info-row"><div className="info-row__label">Innovation Type</div><div className="info-row__value">{c.innovation_type}</div></div>
                  </>
                );
              })()}
            </AnalysisSection>

            <AnalysisSection icon="🌍" title="Market Landscape">
              {(() => {
                const m = analysis.market_landscape || {};
                return (
                  <>
                    <div className="info-row"><div className="info-row__label">Similar Solutions</div><div className="info-row__value">{m.similar_solutions}</div></div>
                    <div className="info-row"><div className="info-row__label">Competition Level</div><div className="info-row__value">{m.competition_level}</div></div>
                    <div className="info-row"><div className="info-row__label">Market Gap</div><div className="info-row__value">{m.market_gap}</div></div>
                  </>
                );
              })()}
            </AnalysisSection>

            <AnalysisSection icon="⚠️" title="How This Can Fail — Know Before You Build">
              {(() => {
                const f = (analysis as any).failure_analysis || {};
                const risks: string[] = f.top_3_kill_risks || [];
                return (
                  <>
                    {f.why_similar_ideas_failed && (
                      <div style={{ marginBottom: "1rem" }}>
                        <div className="info-row__label" style={{ marginBottom: "0.4rem" }}>Why Similar Ideas Have Failed</div>
                        <div style={{
                          padding: "0.9rem 1.1rem",
                          background: "rgba(239,68,68,0.08)",
                          border: "1px solid rgba(239,68,68,0.25)",
                          borderRadius: "10px",
                          fontSize: "0.9rem",
                          lineHeight: 1.65,
                          color: "var(--text-primary)",
                        }}>
                          {f.why_similar_ideas_failed}
                        </div>
                      </div>
                    )}
                    {risks.length > 0 && (
                      <div style={{ marginBottom: "1rem" }}>
                        <div className="info-row__label" style={{ marginBottom: "0.6rem" }}>Top 3 Things That Could Kill This Idea</div>
                        <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                          {risks.map((risk: string, i: number) => (
                            <div key={i} style={{
                              display: "flex", gap: "0.75rem", alignItems: "flex-start",
                              padding: "0.75rem 1rem",
                              background: "rgba(239,68,68,0.06)",
                              border: "1px solid rgba(239,68,68,0.2)",
                              borderRadius: "10px",
                              fontSize: "0.9rem", lineHeight: 1.6, color: "var(--text-primary)",
                            }}>
                              <span style={{ fontWeight: 700, color: "#ef4444", flexShrink: 0, marginTop: "0.05rem" }}>#{i + 1}</span>
                              <span>{risk}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {f.hardest_obstacle_first_90_days && (
                      <div>
                        <div className="info-row__label" style={{ marginBottom: "0.4rem" }}>Hardest Obstacle in the First 90 Days</div>
                        <div style={{
                          padding: "0.9rem 1.1rem",
                          background: "rgba(245,158,11,0.08)",
                          border: "1px solid rgba(245,158,11,0.25)",
                          borderRadius: "10px",
                          fontSize: "0.9rem", lineHeight: 1.65, color: "var(--text-primary)",
                        }}>
                          ⏱️ {f.hardest_obstacle_first_90_days}
                        </div>
                      </div>
                    )}
                  </>
                );
              })()}
            </AnalysisSection>

            <AnalysisSection icon="🤝" title="Support Required">
              {(() => {
                const s = analysis.support_required || {};
                return (
                  <>
                    <div className="info-row"><div className="info-row__label">Team Needed</div><div className="info-row__value">{s.team_needed}</div></div>
                    <div className="info-row"><div className="info-row__label">Funding Stage</div><div className="info-row__value">{s.funding_stage}</div></div>
                    <div className="info-row"><div className="info-row__label">Partnerships</div><div className="info-row__value">{s.partnerships}</div></div>
                    <div className="info-row"><div className="info-row__label">Regulatory</div><div className="info-row__value">{s.regulatory}</div></div>
                  </>
                );
              })()}
            </AnalysisSection>

            <AnalysisSection icon="🛠️" title="Recommended Tech Stack">
              {(() => {
                const t = analysis.tech_stack || {};
                return (
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: "0.75rem" }}>
                    {Object.entries(t).map(([k, v]) => (
                      <div key={k} style={{ padding: "0.75rem", border: "1px solid var(--glass-border)", borderRadius: "10px", background: "rgba(13,17,23,.4)" }}>
                        <div className="info-row__label" style={{ marginBottom: "0.3rem" }}>{k.replace(/_/g, " ").toUpperCase()}</div>
                        <div style={{ fontSize: "0.88rem", color: "var(--text-primary)", fontWeight: 500 }}>{String(v)}</div>
                      </div>
                    ))}
                  </div>
                );
              })()}
            </AnalysisSection>

            {/* ── Downloads ─────────────────────────────────────────── */}
            <div className="card" style={{ marginTop: "2rem" }}>
              <h2 style={{ fontWeight: 700, marginBottom: "1rem" }}>📥 Download Reports</h2>
              <div className="download-bar">
                <button className="btn btn--ghost" onClick={() => handleDownload("json")} disabled={dlLoading === "json"}>
                  {dlLoading === "json" ? "…" : "📦 JSON Report"}
                </button>
                <button className="btn btn--ghost" onClick={() => handleDownload("md")} disabled={dlLoading === "md"}>
                  {dlLoading === "md" ? "…" : "📄 Markdown Report"}
                </button>
                <button className="btn btn--primary" onClick={() => handleDownload("ppt")} disabled={dlLoading === "ppt"}>
                  {dlLoading === "ppt" ? "⏳ Generating…" : "🎯 Download Pitch Deck (.pptx)"}
                </button>
              </div>
            </div>

            {/* ── Follow-up Chat ────────────────────────────────────── */}
            <div className="card" style={{ marginTop: "2rem" }}>
              <h2 style={{ fontWeight: 700, marginBottom: "0.25rem" }}>💬 Ask About Your Report</h2>
              <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginBottom: "1rem" }}>
                Have questions about your analysis? Ask ThynxAI — it knows your full report.
              </p>

              {/* Messages */}
              <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1rem", maxHeight: "360px", overflowY: "auto" }}>
                {followupMessages.length === 0 && (
                  <div style={{ color: "var(--text-muted)", fontSize: "0.85rem", padding: "1rem", textAlign: "center", background: "rgba(255,255,255,0.03)", borderRadius: "10px" }}>
                    e.g. "Why did I score 6 on market feasibility?" · "What should I build first?" · "How do I find investors?"
                  </div>
                )}
                {followupMessages.map((msg, i) => (
                  <div key={i} style={{ display: "flex", justifyContent: msg.role === "user" ? "flex-end" : "flex-start" }}>
                    <div style={{
                      maxWidth: "80%", padding: "0.65rem 1rem",
                      borderRadius: msg.role === "user" ? "14px 14px 4px 14px" : "14px 14px 14px 4px",
                      background: msg.role === "user"
                        ? "linear-gradient(135deg, var(--thynx-blue), #6366f1)"
                        : "rgba(255,255,255,0.06)",
                      color: "var(--text-primary)", fontSize: "0.9rem", lineHeight: 1.55,
                      border: msg.role === "assistant" ? "1px solid var(--glass-border)" : "none",
                    }}>
                      {msg.role === "assistant" && <span style={{ display: "block", fontSize: "0.75rem", color: "var(--thynx-blue-light)", marginBottom: "0.3rem" }}>🤖 ThynxAI</span>}
                      {msg.content}
                    </div>
                  </div>
                ))}
                {followupLoading && (
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "var(--text-muted)", fontSize: "0.83rem" }}>
                    <div className="loading-spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
                    Thinking based on your report…
                  </div>
                )}
              </div>

              {/* Input */}
              <div style={{ display: "flex", gap: "0.6rem" }}>
                <input
                  type="text"
                  value={followupInput}
                  onChange={(e) => setFollowupInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && sendFollowupMsg()}
                  placeholder="Ask about your results…"
                  style={{
                    flex: 1, background: "rgba(255,255,255,0.05)",
                    border: "1px solid var(--glass-border)", borderRadius: "10px",
                    padding: "0.65rem 1rem", color: "var(--text-primary)", fontSize: "0.9rem", outline: "none",
                  }}
                />
                <button
                  className="btn btn--primary"
                  onClick={sendFollowupMsg}
                  disabled={followupLoading || !followupInput.trim()}
                  style={{ minWidth: 80 }}
                >
                  {followupLoading ? "…" : "Ask →"}
                </button>
              </div>
            </div>

            {/* ── Reset ─────────────────────────────────────────────── */}
            <div style={{ textAlign: "center", marginTop: "2rem" }}>
              <button className="btn btn--danger" onClick={handleReset}>
                🔄 Start Over with a New Idea
              </button>
            </div>
          </motion.div>
        )}
      </Layout>
    </>
  );
}
