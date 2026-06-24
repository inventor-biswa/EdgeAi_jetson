/**
 * lib/api.ts — Axios client for ThynxAI Idea Lab API
 * All calls go to FastAPI at port 8000
 */
import axios from "axios";

const BASE = typeof window !== 'undefined' 
  ? `${window.location.protocol}//${window.location.hostname}:8000`
  : process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const client = axios.create({ baseURL: BASE, timeout: 360000 });

// ── Health ────────────────────────────────────────────────────────────────────
export interface HealthResult { status: string; llm: "ready" | "warming_up"; }

export const getHealth = () =>
  client.get<HealthResult>("/health", { timeout: 5000 }).then((r) => r.data);

export interface ValidateResult {
  status: "VALID" | "INVALID";
  reason?: string;
}

export interface QuestionResult {
  question: string;
}

export interface SearchResult {
  search_context: Record<string, string>;
}

export interface AnalysisResult {
  founder_name: string;
  idea_summary: string;
  overall: {
    score: string;
    is_mvp_ready: string;
    is_investment_ready: string;
    is_incubator_ready: string;
    final_verdict: string;
  };
  scores: Record<string, { score: string; reasoning: string }>;
  problem_statement: Record<string, any>;
  proposed_solution: Record<string, any>;
  core_innovation: Record<string, string>;
  market_landscape: Record<string, string>;
  support_required: Record<string, string>;
  tech_stack: Record<string, string>;
  founder_profile?: Record<string, any>;
  followup_qa?: Array<{ question: string; answer: string }>;
  original_idea?: string;
  search_context?: Record<string, any>;
}

export interface ReadinessTips {
  what_it_means: string;
  why_not_ready: string[];
  steps_to_become_ready: string[];
  realistic_timeline: string;
  first_action: string;
  what_investors_look_for?: string[];
}

// ── Step 1 ────────────────────────────────────────────────────────────────────
export const validateIdea = (idea: string) =>
  client.post<ValidateResult>("/api/validate", { idea }).then((r) => r.data);

// ── Step 2→3 bridge ───────────────────────────────────────────────────────────
export const runSearch = (idea: string, founder_data: Record<string, any>) =>
  client
    .post<SearchResult>("/api/search", { idea, founder_data })
    .then((r) => r.data);

// ── Step 3 ────────────────────────────────────────────────────────────────────
export const getNextQuestion = (
  idea: string,
  founder_name: string,
  founder_data: Record<string, any>,
  history: Array<{ question: string; answer: string }>,
  search_context?: Record<string, any>
) =>
  client
    .post<QuestionResult>("/api/question", {
      idea,
      founder_name,
      founder_data,
      history,
      search_context,
    })
    .then((r) => r.data);

// ── Step 4 ────────────────────────────────────────────────────────────────────
export const analyzeIdea = (payload: {
  idea: string;
  founder_name: string;
  founder_data: Record<string, any>;
  followup_qa: Array<{ question: string; answer: string }>;
  search_context?: Record<string, any>;
}) => client.post<AnalysisResult>("/api/analyze", payload).then((r) => r.data);

// ── Sub-pages ─────────────────────────────────────────────────────────────────
export const getReadinessTips = (
  analysis: AnalysisResult,
  readiness_type: "mvp" | "investment",
  search_context?: Record<string, any>
) =>
  client
    .post<ReadinessTips>("/api/readiness", {
      analysis,
      readiness_type,
      search_context,
    })
    .then((r) => r.data);

// ── Downloads ─────────────────────────────────────────────────────────────────
export const downloadJSON = (analysis: AnalysisResult) =>
  client
    .post("/api/report/json", { analysis }, { responseType: "blob" })
    .then((r) => r.data);

export const downloadMarkdown = (analysis: AnalysisResult) =>
  client
    .post("/api/report/md", { analysis }, { responseType: "blob" })
    .then((r) => r.data);

export const downloadPPT = (analysis: AnalysisResult) =>
  client
    .post("/api/ppt", { analysis }, { responseType: "blob" })
    .then((r) => r.data);

export const triggerDownload = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
};

// ── History ───────────────────────────────────────────────────────────────────
export interface AnalysisSummary {
  id: number;
  founder_name: string;
  idea_summary: string;
  score: string;
  saved_at: string;
}

export const getAnalyses = () =>
  client.get<{ analyses: AnalysisSummary[] }>("/api/analyses").then((r) => r.data.analyses);

export const getAnalysis = (id: number) =>
  client.get<AnalysisResult>(`/api/analyses/${id}`).then((r) => r.data);

export const deleteAnalysis = (id: number) =>
  client.delete(`/api/analyses/${id}`).then((r) => r.data);

// ── Chatbot ───────────────────────────────────────────────────────────────────
export interface ChatMessage { role: "user" | "assistant"; content: string; }

export const sendChat = (message: string, history: ChatMessage[]) =>
  client.post<{ reply: string }>("/api/chat", { message, history }).then((r) => r.data.reply);

export const sendFollowup = (
  analysis: AnalysisResult,
  question: string,
  history: ChatMessage[]
) =>
  client
    .post<{ reply: string }>("/api/followup", { analysis, question, history })
    .then((r) => r.data.reply);
