/** components/ChatBubble.tsx — AI and user chat bubbles for founder profile */
import React from "react";
import { motion } from "framer-motion";

interface Props {
  role: "ai" | "user";
  message: string;
  animate?: boolean;
}

export default function ChatBubble({ role, message, animate = true }: Props) {
  const isAI = role === "ai";
  const el = (
    <div
      className={`chat-bubble ${isAI ? "chat-bubble--ai" : "chat-bubble--user"}`}
      style={{ alignSelf: isAI ? "flex-start" : "flex-end" }}
    >
      {isAI && (
        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", marginBottom: "0.4rem" }}>
          <span style={{ fontSize: "0.7rem", color: "var(--thynx-blue-light)", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em" }}>
            🤖 ThynxAI
          </span>
        </div>
      )}
      <div style={{ whiteSpace: "pre-wrap" }}>{message}</div>
    </div>
  );

  if (!animate) return el;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.97 }}
      animate={{ opacity: 1, y: 0,  scale: 1   }}
      transition={{ duration: 0.25 }}
    >
      {el}
    </motion.div>
  );
}
