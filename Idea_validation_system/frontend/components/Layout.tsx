/** components/Layout.tsx — App shell with navbar, footer, and floating chat */
import React from "react";
import Link from "next/link";
import ThynxLogo from "./ThynxLogo";
import StepIndicator from "./StepIndicator";
import ChatWidget from "./ChatWidget";
import { useStore } from "@/lib/store";

interface Props {
  children: React.ReactNode;
  wide?: boolean;
}

export default function Layout({ children, wide }: Props) {
  const { state } = useStore();

  return (
    <div className="page-container">
      <nav className="navbar">
        <Link href="/" className="navbar__brand">
          <ThynxLogo size="sm" />
        </Link>
        <span className="navbar__powered">
          ⚡ Jetson Offline · AI Powered
        </span>
      </nav>

      <StepIndicator currentStep={state.step} />

      <main className={`main-content ${wide ? "main-content--wide" : ""}`}>
        {children}
      </main>

      <footer className="footer">
        © {new Date().getFullYear()} ThynxAI — Beyond Intelligence &nbsp;·&nbsp; Powered by Qwen 2.5 on NVIDIA Jetson
      </footer>

      {/* Floating AI chatbot — available on every page */}
      <ChatWidget />
    </div>
  );
}
