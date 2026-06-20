import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { sendChat, ChatMessage } from "@/lib/api";

const SendIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="2" x2="11" y2="13"></line>
    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
  </svg>
);

const ChatIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
  </svg>
);

const CloseIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="6" x2="6" y2="18"></line>
    <line x1="6" y1="6" x2="18" y2="18"></line>
  </svg>
);

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, open]);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;
    const userMsg: ChatMessage = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const reply = await sendChat(text, [...messages, userMsg]);
      setMessages((prev) => [...prev, { role: "assistant", content: reply }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "⚠️ Could not reach the AI. Is the backend running?" },
      ]);
    }
    setLoading(false);
  };

  return (
    <>
      {/* Floating button */}
      <motion.button
        id="chat-widget-btn"
        onClick={() => setOpen((o) => !o)}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        style={{
          position: "fixed", bottom: "2rem", right: "2rem", zIndex: 1000,
          width: 60, height: 60, borderRadius: "50%",
          background: "linear-gradient(135deg, #4f46e5, #8b5cf6)",
          border: "1px solid rgba(255,255,255,0.2)",
          cursor: "pointer", display: "flex",
          alignItems: "center", justifyContent: "center",
          boxShadow: "0 10px 30px rgba(99, 102, 241, 0.5)",
          color: "#ffffff", transition: "box-shadow 0.3s ease",
        }}
        title="Ask ThynxAI"
      >
        <AnimatePresence mode="wait">
          {open ? (
            <motion.div key="close" initial={{ opacity: 0, rotate: -90 }} animate={{ opacity: 1, rotate: 0 }} exit={{ opacity: 0, rotate: 90 }} transition={{ duration: 0.2 }}>
              <CloseIcon />
            </motion.div>
          ) : (
            <motion.div key="chat" initial={{ opacity: 0, rotate: 90 }} animate={{ opacity: 1, rotate: 0 }} exit={{ opacity: 0, rotate: -90 }} transition={{ duration: 0.2 }}>
              <ChatIcon />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.button>

      {/* Chat panel */}
      <AnimatePresence>
        {open && (
          <motion.div
            id="chat-widget-panel"
            initial={{ opacity: 0, y: 30, scale: 0.9, filter: "blur(10px)" }}
            animate={{ opacity: 1, y: 0, scale: 1, filter: "blur(0px)" }}
            exit={{ opacity: 0, y: 20, scale: 0.95, filter: "blur(5px)" }}
            transition={{ type: "spring", stiffness: 350, damping: 25 }}
            style={{
              position: "fixed", bottom: "6.5rem", right: "2rem", zIndex: 999,
              width: "min(400px, calc(100vw - 3rem))",
              height: "min(600px, 75vh)",
              background: "rgba(18, 18, 28, 0.75)",
              backdropFilter: "blur(24px) saturate(180%)",
              WebkitBackdropFilter: "blur(24px) saturate(180%)",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              borderRadius: "24px",
              display: "flex", flexDirection: "column",
              boxShadow: "0 24px 64px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.1)",
              overflow: "hidden",
            }}
          >
            {/* Header */}
            <div style={{
              padding: "1.2rem 1.5rem",
              background: "rgba(255, 255, 255, 0.03)",
              borderBottom: "1px solid rgba(255, 255, 255, 0.06)",
              display: "flex", alignItems: "center", gap: "0.8rem",
            }}>
              <div style={{
                width: 40, height: 40, borderRadius: "12px",
                background: "linear-gradient(135deg, #4f46e5, #8b5cf6)",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: "1.3rem", boxShadow: "0 4px 12px rgba(99, 102, 241, 0.4)"
              }}>
                🤖
              </div>
              <div>
                <div style={{ fontWeight: 700, fontSize: "1.05rem", color: "#fff", letterSpacing: "0.3px" }}>
                  ThynxAI
                </div>
                <div style={{ fontSize: "0.75rem", color: "rgba(255,255,255,0.6)", display: "flex", alignItems: "center", gap: "4px" }}>
                  <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#10b981", display: "inline-block", boxShadow: "0 0 8px #10b981" }} />
                  Offline · Powered by Qwen
                </div>
              </div>
            </div>

            {/* Messages */}
            <div style={{
              flex: 1, overflowY: "auto", padding: "1.5rem",
              display: "flex", flexDirection: "column", gap: "1rem",
              scrollbarWidth: "none" // For Firefox
            }}>
              <style>{`#chat-widget-panel ::-webkit-scrollbar { display: none; }`}</style>
              
              {messages.length === 0 && (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
                  style={{ textAlign: "center", color: "rgba(255,255,255,0.5)", fontSize: "0.9rem", marginTop: "3rem", lineHeight: 1.6 }}>
                  <div style={{ fontSize: "3rem", marginBottom: "1rem", filter: "drop-shadow(0 4px 12px rgba(0,0,0,0.2))" }}>✨</div>
                  Hello! I'm your secure, offline startup mentor.<br/>Ask me anything about your idea.
                </motion.div>
              )}
              
              {messages.map((msg, i) => (
                <motion.div key={i} initial={{ opacity: 0, y: 10, scale: 0.95 }} animate={{ opacity: 1, y: 0, scale: 1 }}
                  style={{
                    display: "flex",
                    justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
                  }}>
                  <div style={{
                    maxWidth: "85%", padding: "0.8rem 1.1rem",
                    borderRadius: msg.role === "user" ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
                    background: msg.role === "user"
                      ? "linear-gradient(135deg, #4f46e5, #7c3aed)"
                      : "rgba(255, 255, 255, 0.05)",
                    color: "#fff", fontSize: "0.92rem", lineHeight: 1.5,
                    border: msg.role === "assistant" ? "1px solid rgba(255,255,255,0.08)" : "none",
                    boxShadow: msg.role === "user" ? "0 4px 12px rgba(99, 102, 241, 0.3)" : "none",
                  }}>
                    {msg.content}
                  </div>
                </motion.div>
              ))}
              
              {loading && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                  style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "rgba(255,255,255,0.5)", fontSize: "0.85rem" }}>
                  <div className="loading-spinner" style={{ width: 14, height: 14, borderWidth: 2, borderColor: "rgba(255,255,255,0.2)", borderTopColor: "#fff" }} />
                  Thinking…
                </motion.div>
              )}
              <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div style={{
              padding: "1rem 1.2rem", background: "rgba(0,0,0,0.2)",
              borderTop: "1px solid rgba(255, 255, 255, 0.06)",
            }}>
              <div style={{
                display: "flex", gap: "0.6rem", background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255, 255, 255, 0.1)", borderRadius: "16px",
                padding: "0.4rem", transition: "border-color 0.2s",
              }}
              onFocus={(e) => e.currentTarget.style.borderColor = "rgba(99, 102, 241, 0.5)"}
              onBlur={(e) => e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.1)"}
              >
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && send()}
                  placeholder="Ask anything…"
                  style={{
                    flex: 1, background: "transparent", border: "none",
                    padding: "0.5rem 0.8rem", color: "#fff", fontSize: "0.95rem",
                    outline: "none",
                  }}
                  autoFocus
                />
                <motion.button
                  onClick={send}
                  disabled={loading || !input.trim()}
                  whileHover={{ scale: (loading || !input.trim()) ? 1 : 1.05 }}
                  whileTap={{ scale: (loading || !input.trim()) ? 1 : 0.95 }}
                  style={{
                    width: 42, height: 42, borderRadius: "12px",
                    background: (loading || !input.trim()) ? "rgba(255,255,255,0.05)" : "linear-gradient(135deg, #4f46e5, #8b5cf6)",
                    border: "none", color: (loading || !input.trim()) ? "rgba(255,255,255,0.3)" : "#fff",
                    cursor: (loading || !input.trim()) ? "default" : "pointer",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    boxShadow: (loading || !input.trim()) ? "none" : "0 4px 12px rgba(99, 102, 241, 0.4)",
                    transition: "all 0.3s ease",
                  }}
                >
                  <SendIcon />
                </motion.button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
