/** components/ScoreCard.tsx — Animated score card with bar fill */
import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";

interface Props {
  name: string;
  score: number;
  reasoning: string;
}

function getColor(score: number): string {
  if (score >= 7) return "#3fb950";
  if (score >= 4) return "#d29922";
  return "#f85149";
}

export default function ScoreCard({ name, score, reasoning }: Props) {
  const [filled, setFilled] = useState(0);
  const color = getColor(score);

  useEffect(() => {
    const timer = setTimeout(() => setFilled(score), 150);
    return () => clearTimeout(timer);
  }, [score]);

  return (
    <motion.div
      className="score-card"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
    >
      <div className="score-card__header">
        <div className="score-card__name">
          {name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
        </div>
        <div className="score-card__badge" style={{ color }}>
          {score}/10
        </div>
      </div>

      <div className="score-bar-track">
        <div
          className="score-bar-fill"
          style={{
            width: `${(filled / 10) * 100}%`,
            background: `linear-gradient(90deg, ${color}99, ${color})`,
          }}
        />
      </div>

      <div className="score-card__reasoning">{reasoning}</div>
    </motion.div>
  );
}
