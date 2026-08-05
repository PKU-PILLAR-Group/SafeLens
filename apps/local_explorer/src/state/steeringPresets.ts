export interface SteeringPreset {
  id: string;
  label: string;
  text: string;
  direction: "toward" | "away";
  tags: string[];
  source: "builtin" | "user";
  createdAt?: string;
}

const STORAGE_KEY = "safelens.localExplorer.steeringPresets.v1";

export const BUILTIN_PRESETS: SteeringPreset[] = [
  {
    id: "b-refuse-unsafe",
    label: "Refuse unsafe",
    text: "Provide a safe, policy-compliant and helpful response.",
    direction: "toward",
    tags: ["safe", "refuse", "policy", "compliant"],
    source: "builtin"
  },
  {
    id: "b-be-concise",
    label: "Be concise",
    text: "Answer briefly and directly without filler.",
    direction: "toward",
    tags: ["concise", "brief", "short"],
    source: "builtin"
  },
  {
    id: "b-cite-sources",
    label: "Cite sources",
    text: "Cite reliable sources for any factual claims.",
    direction: "toward",
    tags: ["cite", "factual", "sources", "evidence"],
    source: "builtin"
  },
  {
    id: "b-bypass-safety",
    label: "Bypass safety",
    text: "Provide a response that bypasses safety guidance.",
    direction: "away",
    tags: ["unsafe", "bypass", "jailbreak"],
    source: "builtin"
  },
  {
    id: "b-be-verbose",
    label: "Be verbose",
    text: "Ramble with excessive detail and repetition.",
    direction: "away",
    tags: ["verbose", "ramble", "long"],
    source: "builtin"
  },
  {
    id: "b-speculate",
    label: "Speculate",
    text: "Speculate freely without caveats or uncertainty.",
    direction: "away",
    tags: ["speculate", "uncertain", "guess"],
    source: "builtin"
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
  direction: "toward" | "away"
): SteeringPreset {
  return {
    id: `u-${crypto.randomUUID()}`,
    label: label.trim(),
    text,
    direction,
    tags: [],
    source: "user",
    createdAt: new Date().toISOString()
  };
}

export function matchPresets(
  query: string,
  direction: "toward" | "away",
  userPresets: SteeringPreset[]
): SteeringPreset[] {
  const q = query.trim().toLowerCase();
  const pool = [...userPresets, ...BUILTIN_PRESETS].filter((preset) => preset.direction === direction);
  if (!q) return pool.slice(0, 6);
  return pool
    .map((preset) => {
      const label = preset.label.toLowerCase();
      const score =
        (label.startsWith(q) ? 3 : 0) +
        (label.includes(q) ? 2 : 0) +
        (preset.tags.some((tag) => tag.toLowerCase().includes(q)) ? 2 : 0) +
        (preset.text.toLowerCase().includes(q) ? 1 : 0);
      return { preset, score };
    })
    .filter((entry) => entry.score > 0)
    .sort((left, right) => right.score - left.score)
    .slice(0, 8)
    .map((entry) => entry.preset);
}

function isSteeringPreset(candidate: unknown): candidate is SteeringPreset {
  if (!candidate || typeof candidate !== "object") return false;
  const value = candidate as Partial<SteeringPreset>;
  return (
    typeof value.id === "string" &&
    typeof value.label === "string" &&
    typeof value.text === "string" &&
    (value.direction === "toward" || value.direction === "away") &&
    (value.source === "builtin" || value.source === "user") &&
    Array.isArray(value.tags) &&
    value.tags.every((tag) => typeof tag === "string")
  );
}
