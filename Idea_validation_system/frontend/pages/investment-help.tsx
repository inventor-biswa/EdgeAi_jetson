/** pages/investment-help.tsx — Sub-page: Investment Readiness Roadmap */
import React, { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Head from "next/head";
import { motion, AnimatePresence } from "framer-motion";
import Layout from "@/components/Layout";
import LoadingOverlay from "@/components/LoadingOverlay";
import { useStore } from "@/lib/store";
import { getReadinessTips, ReadinessTips } from "@/lib/api";

export default function InvestmentHelp() {
  const router = useRouter();
  const { state } = useStore();
  const [tips, setTips] = useState<ReadinessTips | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!state.analysis) { router.replace("/results"); return; }
    setLoading(true);
    getReadinessTips(state.analysis, "investment", state.searchContext || undefined)
      .then(setTips)
      .catch(() => setError("Could not generate investment tips. Please try again."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <Head><title>Investment Readiness — ThynxAI Idea Lab</title></Head>
      <AnimatePresence>{loading && <LoadingOverlay message="Generating your investment roadmap…" />}</AnimatePresence>

      <Layout>
        <button className="btn btn--ghost" onClick={() => router.back()} style={{ marginBottom: "1.5rem" }}>
          ← Back to Report
        </button>

        <div className="page-header">
          <div className="page-header__tag">💰 Investment Readiness</div>
          <h1 className="page-header__title">How to Become Investment Ready</h1>
          <p className="page-header__sub">AI-generated steps tailored specifically to your idea.</p>
        </div>

        {error && <div className="alert alert--error">{error}</div>}

        {tips && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <div className="card" style={{ marginBottom: "1.25rem" }}>
              <h2 style={{ fontWeight: 700, marginBottom: "0.75rem" }}>📌 What Investment Ready means</h2>
              <div className="alert alert--info">{tips.what_it_means}</div>
            </div>

            {tips.why_not_ready?.length > 0 && (
              <div className="card" style={{ marginBottom: "1.25rem" }}>
                <h2 style={{ fontWeight: 700, marginBottom: "0.75rem" }}>❌ Why it's not Investment Ready yet</h2>
                <ul className="bullet-list">
                  {tips.why_not_ready.map((pt, i) => <li key={i}>{pt}</li>)}
                </ul>
              </div>
            )}

            {tips.steps_to_become_ready?.length > 0 && (
              <div className="card" style={{ marginBottom: "1.25rem" }}>
                <h2 style={{ fontWeight: 700, marginBottom: "0.75rem" }}>✅ Steps to become Investment Ready</h2>
                <ol style={{ paddingLeft: "1.25rem", display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                  {tips.steps_to_become_ready.map((step, i) => (
                    <li key={i} style={{ fontSize: "0.95rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>
                      <strong style={{ color: "var(--text-primary)" }}>{i + 1}.</strong> {step}
                    </li>
                  ))}
                </ol>
              </div>
            )}

            {tips.what_investors_look_for && tips.what_investors_look_for.length > 0 && (
              <div className="card" style={{ marginBottom: "1.25rem" }}>
                <h2 style={{ fontWeight: 700, marginBottom: "0.75rem" }}>👀 What Investors Look For</h2>
                <ul className="bullet-list">
                  {tips.what_investors_look_for.map((pt, i) => <li key={i}>{pt}</li>)}
                </ul>
              </div>
            )}

            <div className="card" style={{ marginBottom: "1.25rem" }}>
              <h2 style={{ fontWeight: 700, marginBottom: "0.5rem" }}>⏰ Realistic Timeline</h2>
              <p style={{ color: "var(--text-secondary)" }}>{tips.realistic_timeline}</p>
            </div>

            {tips.first_action && (
              <div className="alert alert--success" style={{ fontSize: "1rem", fontWeight: 600 }}>
                🚀 First thing to do tomorrow: {tips.first_action}
              </div>
            )}
          </motion.div>
        )}
      </Layout>
    </>
  );
}
