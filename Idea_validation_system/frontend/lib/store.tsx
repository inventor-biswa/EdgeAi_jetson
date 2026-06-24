/**
 * lib/store.tsx — React Context for global app state
 * Persists to localStorage so page refreshes don't lose data.
 */
import React, {
  createContext,
  useContext,
  useReducer,
  useEffect,
  ReactNode,
} from "react";
import { AnalysisResult, ReadinessTips } from "./api";

// ─── State Shape ──────────────────────────────────────────────────────────────
export interface AppState {
  step: 1 | 2 | 3 | 4;
  idea: string;
  founderData: Record<string, any>;
  chatHistory: Array<{ question: string; answer: string }>;
  chatIndex: number;
  questions: string[];
  currentQuestionIndex: number;
  answersHistory: Array<{ question: string; answer: string }>;
  followupQA: Array<{ question: string; answer: string }>;
  analysis: AnalysisResult | null;
  analysisId: number | null;
  searchContext: Record<string, any> | null;
  subPage: "mvp_help" | "investment_help" | null;
  mvpTips: ReadinessTips | null;
  investmentTips: ReadinessTips | null;
}

const INITIAL_STATE: AppState = {
  step: 1,
  idea: "",
  founderData: {},
  chatHistory: [],
  chatIndex: 0,
  questions: [],
  currentQuestionIndex: 0,
  answersHistory: [],
  followupQA: [],
  analysis: null,
  analysisId: null,
  searchContext: null,
  subPage: null,
  mvpTips: null,
  investmentTips: null,
};

// ─── Actions ──────────────────────────────────────────────────────────────────
type Action =
  | { type: "SET_STEP"; payload: 1 | 2 | 3 | 4 }
  | { type: "SET_IDEA"; payload: string }
  | { type: "SAVE_FOUNDER_ANSWER"; key: string; answer: string; question: string }
  | { type: "GO_BACK_CHAT" }
  | { type: "SET_SEARCH_CONTEXT"; payload: Record<string, any> }
  | { type: "ADD_QUESTION"; payload: string }
  | { type: "SAVE_QUESTION_ANSWER"; question: string; answer: string }
  | { type: "SET_ANALYSIS"; payload: AnalysisResult }
  | { type: "SET_SUB_PAGE"; payload: "mvp_help" | "investment_help" | null }
  | { type: "SET_MVP_TIPS"; payload: ReadinessTips }
  | { type: "SET_INVESTMENT_TIPS"; payload: ReadinessTips }
  | { type: "LOAD_SAVED_ANALYSIS"; payload: AnalysisResult }
  | { type: "RESET" }
  | { type: "START_NEW_IDEA"; payload: string };

function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case "SET_STEP":
      return { ...state, step: action.payload };
    case "SET_IDEA":
      return { ...state, idea: action.payload };
    case "SAVE_FOUNDER_ANSWER": {
      const newHistory = [
        ...state.chatHistory,
        { question: action.question, answer: action.answer },
      ];
      const newData = { ...state.founderData, [action.key]: action.answer };
      return {
        ...state,
        chatHistory: newHistory,
        founderData: newData,
        chatIndex: state.chatIndex + 1,
      };
    }
    case "GO_BACK_CHAT": {
      if (state.chatIndex === 0) return state;
      const newHistory = state.chatHistory.slice(0, -1);
      const keys = Object.keys(state.founderData);
      const newData = { ...state.founderData };
      if (keys.length > 0) delete newData[keys[keys.length - 1]];
      return {
        ...state,
        chatHistory: newHistory,
        founderData: newData,
        chatIndex: state.chatIndex - 1,
      };
    }
    case "SET_SEARCH_CONTEXT":
      return { ...state, searchContext: action.payload };
    case "ADD_QUESTION":
      return { ...state, questions: [...state.questions, action.payload] };
    case "SAVE_QUESTION_ANSWER": {
      const newAnswers = [
        ...state.answersHistory,
        { question: action.question, answer: action.answer },
      ];
      const nextIndex = state.currentQuestionIndex + 1;
      // 3 fixed + 3 AI-generated = 6 total questions before analysis
      if (nextIndex > 5) {
        return {
          ...state,
          answersHistory: newAnswers,
          followupQA: newAnswers,
          step: 4,
        };
      }
      return {
        ...state,
        answersHistory: newAnswers,
        currentQuestionIndex: nextIndex,
      };
    }
    case "SET_ANALYSIS":
      return {
        ...state,
        analysis: action.payload,
        analysisId: action.payload.id ?? null,
      };
    case "SET_SUB_PAGE":
      return { ...state, subPage: action.payload };
    case "SET_MVP_TIPS":
      return { ...state, mvpTips: action.payload };
    case "SET_INVESTMENT_TIPS":
      return { ...state, investmentTips: action.payload };
    case "LOAD_SAVED_ANALYSIS":
      // Load a historical analysis — restore any tips that were saved alongside it
      return {
        ...INITIAL_STATE,
        step: 4,
        analysis: action.payload,
        analysisId: action.payload.id ?? null,
        idea: action.payload.original_idea || action.payload.idea_summary || "",
        mvpTips: action.payload.mvp_tips ?? null,
        investmentTips: action.payload.investment_tips ?? null,
      };
    case "RESET":
      return { ...INITIAL_STATE };
    case "START_NEW_IDEA":
      return { ...INITIAL_STATE, idea: action.payload, step: 2 };
    default:
      return state;
  }
}

// ─── Context ──────────────────────────────────────────────────────────────────
const StoreContext = createContext<{
  state: AppState;
  dispatch: React.Dispatch<Action>;
} | null>(null);

const STORAGE_KEY = "thynxai_state";

export function StoreProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE, () => {
    if (typeof window === "undefined") return INITIAL_STATE;
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? { ...INITIAL_STATE, ...JSON.parse(saved) } : INITIAL_STATE;
    } catch {
      return INITIAL_STATE;
    }
  });

  // Persist to localStorage on every state change
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {}
  }, [state]);

  return (
    <StoreContext.Provider value={{ state, dispatch }}>
      {children}
    </StoreContext.Provider>
  );
}

export function useStore() {
  const ctx = useContext(StoreContext);
  if (!ctx) throw new Error("useStore must be used inside StoreProvider");
  return ctx;
}
