/** components/AnalysisSection.tsx — Collapsible card for each report section */
import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface Props {
  icon: string;
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

export default function AnalysisSection({
  icon,
  title,
  children,
  defaultOpen = false,
}: Props) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="analysis-section">
      <div
        className={`analysis-section__header ${open ? "analysis-section__header--open" : ""}`}
        onClick={() => setOpen((o) => !o)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === "Enter" && setOpen((o) => !o)}
      >
        <div className="analysis-section__title">
          <span>{icon}</span>
          <span>{title}</span>
        </div>
        <svg
          className={`analysis-section__chevron ${open ? "analysis-section__chevron--open" : ""}`}
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
        >
          <path d="M4 6l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </div>

      <AnimatePresence>
        {open && (
          <motion.div
            className="analysis-section__body"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.28, ease: "easeInOut" }}
            style={{ overflow: "hidden" }}
          >
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
