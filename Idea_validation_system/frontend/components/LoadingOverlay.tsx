/** components/LoadingOverlay.tsx — Full-screen AI thinking overlay */
import React from "react";
import { motion } from "framer-motion";

interface Props {
  message?: string;
}

const MESSAGES = [
  "Consulting the AI oracle…",
  "Crunching market data…",
  "Thinking hard about your idea…",
  "Analyzing competitive landscape…",
  "Almost there, hold tight…",
];

export default function LoadingOverlay({
  message = "Analyzing your idea…",
}: Props) {
  return (
    <motion.div
      className="loading-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <div style={{ position: "relative" }}>
        {/* Outer glow ring */}
        <motion.div
          style={{
            position: "absolute",
            inset: "-12px",
            borderRadius: "50%",
            border: "1px solid rgba(67,97,238,.3)",
          }}
          animate={{ scale: [1, 1.15, 1], opacity: [0.5, 0.15, 0.5] }}
          transition={{ repeat: Infinity, duration: 2 }}
        />
        <div className="loading-spinner" />
      </div>

      <div style={{ textAlign: "center" }}>
        <div className="loading-text" style={{ fontWeight: 600, fontSize: "1.05rem", color: "var(--text-primary)", marginBottom: "0.4rem" }}>
          {message}
        </div>
        <div className="loading-text loading-dots" style={{ color: "var(--text-secondary)" }}>
          This may take a minute on the Jetson
        </div>
      </div>

      {/* Thynx logo watermark */}
      <div style={{ position: "absolute", bottom: "2rem", opacity: 0.3, fontSize: "0.75rem", letterSpacing: "0.15em", color: "var(--text-muted)", textTransform: "uppercase" }}>
        ThynxAI · Powered by Qwen 2.5
      </div>
    </motion.div>
  );
}
