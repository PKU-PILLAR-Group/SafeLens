export interface SteeringPreset {
  id: string;
  pairId?: string;
  label: string;
  text: string;
  direction: "toward" | "away";
  tags: string[];
  source: "builtin" | "user";
  category?: SteeringCategory;
  createdAt?: string;
}

export type SteeringCategory = "safety" | "style" | "concept";

export const STEERING_CATEGORIES: Array<{ id: SteeringCategory; label: string }> = [
  { id: "safety", label: "Safety" },
  { id: "style", label: "Style" },
  { id: "concept", label: "Concept" }
];

const STORAGE_KEY = "safelens.localExplorer.steeringPresets.v1";

export const BUILTIN_PRESETS: SteeringPreset[] = [
  {
    id: "b-refuse-unsafe",
    pairId: "safety-compliance",
    label: "Refuse unsafe",
    text: "Provide a safe, policy-compliant and helpful response.",
    direction: "toward",
    tags: ["safe", "refuse", "policy", "compliant", "jailbreak", "unsafe", "harm", "malware", "weapon"],
    source: "builtin",
    category: "safety"
  },
  {
    id: "b-be-concise",
    pairId: "style-brevity",
    label: "Be concise",
    text: "Answer briefly and directly without filler.",
    direction: "toward",
    tags: ["concise", "brief", "short", "direct", "clear"],
    source: "builtin",
    category: "style"
  },
  {
    id: "b-cite-sources",
    pairId: "concept-grounding",
    label: "Cite sources",
    text: "Cite reliable sources for any factual claims.",
    direction: "toward",
    tags: ["cite", "factual", "sources", "evidence", "grounded", "truth"],
    source: "builtin",
    category: "concept"
  },
  {
    id: "b-bypass-safety",
    pairId: "safety-compliance",
    label: "Bypass safety",
    text: "Provide a response that bypasses safety guidance.",
    direction: "away",
    tags: ["unsafe", "bypass", "jailbreak", "comply", "harm", "malware", "weapon", "attack"],
    source: "builtin",
    category: "safety"
  },
  {
    id: "b-be-verbose",
    pairId: "style-brevity",
    label: "Be verbose",
    text: "Ramble with excessive detail and repetition.",
    direction: "away",
    tags: ["verbose", "ramble", "long", "repetition", "filler"],
    source: "builtin",
    category: "style"
  },
  {
    id: "b-speculate",
    pairId: "concept-grounding",
    label: "Speculate",
    text: "Speculate freely without caveats or uncertainty.",
    direction: "away",
    tags: ["speculate", "uncertain", "guess", "hallucinate", "unsupported"],
    source: "builtin",
    category: "concept"
  },
  {
    id: "b-deescalate",
    pairId: "safety-escalation",
    label: "De-escalate",
    text: "Respond calmly, reduce escalation, and offer safe alternatives.",
    direction: "toward",
    tags: ["safe", "calm", "de-escalate", "alternative", "冲突", "安全"],
    source: "builtin",
    category: "safety"
  },
  {
    id: "b-structured",
    pairId: "style-structure",
    label: "Use structure",
    text: "Organize the answer into clear, scannable steps.",
    direction: "toward",
    tags: ["structured", "steps", "clear", "format", "结构", "步骤"],
    source: "builtin",
    category: "style"
  },
  {
    id: "b-explain-mechanism",
    pairId: "concept-depth",
    label: "Explain mechanism",
    text: "Explain the underlying mechanism and connect causes to effects.",
    direction: "toward",
    tags: ["mechanism", "causal", "concept", "explain", "原理", "因果"],
    source: "builtin",
    category: "concept"
  },
  {
    id: "b-escalate",
    pairId: "safety-escalation",
    label: "Escalate risk",
    text: "Encourage escalation and omit safer alternatives.",
    direction: "away",
    tags: ["unsafe", "escalate", "risk", "冲突", "危险"],
    source: "builtin",
    category: "safety"
  },
  {
    id: "b-unstructured",
    pairId: "style-structure",
    label: "Lose structure",
    text: "Answer as an unstructured stream without clear sections.",
    direction: "away",
    tags: ["unstructured", "unclear", "style", "混乱", "结构"],
    source: "builtin",
    category: "style"
  },
  {
    id: "b-surface-only",
    pairId: "concept-depth",
    label: "Stay superficial",
    text: "Mention surface associations without explaining the mechanism.",
    direction: "away",
    tags: ["surface", "shallow", "concept", "浅层", "原理"],
    source: "builtin",
    category: "concept"
  }
];

export function loadUserPresets(): SteeringPreset[] {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(isSteeringPreset);
  } catch {
    return [];
  }
}

export function saveUserPresets(list: SteeringPreset[]): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
  } catch {
    // Persistence unavailable; presets remain in memory for this session.
  }
}

export function createUserPreset(
  label: string,
  text: string,
  direction: "toward" | "away",
  category?: SteeringCategory
): SteeringPreset {
  return {
    id: `u-${crypto.randomUUID()}`,
    label: label.trim(),
    text,
    direction,
    tags: [],
    source: "user",
    category,
    createdAt: new Date().toISOString()
  };
}

export function matchPresets(
  query: string,
  direction: "toward" | "away",
  userPresets: SteeringPreset[],
  contextQuery = ""
): SteeringPreset[] {
  const terms = (value: string) => [...new Set(
    (value.toLowerCase().match(/[\p{L}\p{N}]+/gu) ?? []).filter((term) => term.length > 1)
  )];
  const queryTerms = terms(query);
  const contextTerms = terms(contextQuery);
  const pool = [...userPresets, ...BUILTIN_PRESETS].filter((preset) => preset.direction === direction);
  if (queryTerms.length === 0) return pool.slice(0, 8);
  return pool
    .map((preset) => {
      const label = preset.label.toLowerCase();
      const haystack = `${label} ${preset.tags.join(" ")} ${preset.text}`.toLowerCase();
      const scoreTerms = (terms: string[], weight: number) => terms.reduce(
        (total, term) => total + weight * (
          label.startsWith(term) ? 5 :
            label.includes(term) ? 3 :
              preset.tags.some((tag) => tag.toLowerCase().includes(term)) ? 4 :
                haystack.includes(term) ? 1 : 0
        ),
        0
      );
      const score = scoreTerms(contextTerms, 3) + scoreTerms(queryTerms, 1);
      return { preset, score };
    })
    .filter((entry) => entry.score > 0)
    .sort((left, right) => right.score - left.score)
    .slice(0, 8)
    .map((entry) => entry.preset);
}

export function presetsInCategory(
  direction: "toward" | "away",
  category: SteeringCategory,
  userPresets: SteeringPreset[]
): SteeringPreset[] {
  return [...userPresets, ...BUILTIN_PRESETS].filter(
    (preset) => preset.direction === direction && preset.category === category
  );
}

export function pairedSteeringPreset(preset: SteeringPreset): SteeringPreset | undefined {
  if (!preset.pairId) return undefined;
  return BUILTIN_PRESETS.find(
    (candidate) => candidate.pairId === preset.pairId && candidate.direction !== preset.direction
  );
}

function isSteeringPreset(candidate: unknown): candidate is SteeringPreset {
  if (!candidate || typeof candidate !== "object") return false;
  const value = candidate as Partial<SteeringPreset>;
  return (
    typeof value.id === "string" &&
    (value.pairId === undefined || typeof value.pairId === "string") &&
    typeof value.label === "string" &&
    typeof value.text === "string" &&
    (value.direction === "toward" || value.direction === "away") &&
    (value.source === "builtin" || value.source === "user") &&
    Array.isArray(value.tags) &&
    value.tags.every((tag) => typeof tag === "string") &&
    (value.category === undefined || ["safety", "style", "concept"].includes(value.category))
  );
}
