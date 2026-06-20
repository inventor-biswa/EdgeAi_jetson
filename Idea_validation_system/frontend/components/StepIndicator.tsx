/** components/StepIndicator.tsx — Animated 4-step progress bar */
import React from "react";
import { motion } from "framer-motion";

interface Props {
  currentStep: 1 | 2 | 3 | 4;
}

const STEPS = [
  { num: 1, label: "Idea" },
  { num: 2, label: "Profile" },
  { num: 3, label: "Questions" },
  { num: 4, label: "Results" },
];

export default function StepIndicator({ currentStep }: Props) {
  return (
    <div className="step-indicator">
      {STEPS.map((step, i) => {
        const done   = currentStep > step.num;
        const active = currentStep === step.num;
        return (
          <React.Fragment key={step.num}>
            <div className="step-indicator__item">
              <motion.div
                className={`step-indicator__dot ${
                  done   ? "step-indicator__dot--done" :
                  active ? "step-indicator__dot--active" : ""
                }`}
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1,   opacity: 1  }}
                transition={{ delay: i * 0.08 }}
              >
                {done ? "✓" : step.num}
              </motion.div>
              <span
                className={`step-indicator__label ${
                  done   ? "step-indicator__label--done" :
                  active ? "step-indicator__label--active" : ""
                }`}
              >
                {step.label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div
                className={`step-indicator__line ${done ? "step-indicator__line--done" : ""}`}
              />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}
