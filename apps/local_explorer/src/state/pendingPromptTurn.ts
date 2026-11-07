const PENDING_PROMPT_STORAGE_KEY = "safelens.localExplorer.pendingPrompt.v1";

export interface PendingPromptTurn {
  turnId: string;
  prompt: string;
  jobId: string;
  conversationId: string;
  model: string;
  maxNewTokens: number;
  startedAt: string;
}

export function loadPendingPromptTurn(): PendingPromptTurn | null {
  try {
    const raw = window.localStorage.getItem(PENDING_PROMPT_STORAGE_KEY);
    if (!raw) return null;
    const value: unknown = JSON.parse(raw);
    if (!value || typeof value !== "object" || Array.isArray(value)) return null;
    const record = value as Record<string, unknown>;
    if (
      typeof record.turnId !== "string" ||
      typeof record.prompt !== "string" ||
      typeof record.jobId !== "string" ||
      typeof record.conversationId !== "string" ||
      typeof record.model !== "string" ||
      typeof record.maxNewTokens !== "number" ||
      typeof record.startedAt !== "string"
    ) {
      return null;
    }
    return {
      turnId: record.turnId,
      prompt: record.prompt,
      jobId: record.jobId,
      conversationId: record.conversationId,
      model: record.model,
      maxNewTokens: record.maxNewTokens,
      startedAt: record.startedAt
    };
  } catch {
    return null;
  }
}

export function savePendingPromptTurn(value: PendingPromptTurn) {
  try {
    window.localStorage.setItem(PENDING_PROMPT_STORAGE_KEY, JSON.stringify(value));
  } catch {
    // Recovery is best-effort; storage may be unavailable in private mode.
  }
}

export function clearPendingPromptTurn() {
  try {
    window.localStorage.removeItem(PENDING_PROMPT_STORAGE_KEY);
  } catch {
    // Best-effort cleanup.
  }
}
