/** lib/useAIStatus.ts — polls /health so the UI can show "AI is warming up"
 * instead of a hard error during the ~90s post-restart model load window. */
import { useEffect, useState } from "react";
import { getHealth } from "./api";

export type AIStatus = "checking" | "ready" | "warming_up" | "down";

export function useAIStatus(pollMs = 5000): AIStatus {
  const [status, setStatus] = useState<AIStatus>("checking");

  useEffect(() => {
    let cancelled = false;

    const check = async () => {
      try {
        const { llm } = await getHealth();
        if (!cancelled) setStatus(llm === "ready" ? "ready" : "warming_up");
      } catch {
        if (!cancelled) setStatus("down");
      }
    };

    check();
    const id = setInterval(check, pollMs);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [pollMs]);

  return status;
}
