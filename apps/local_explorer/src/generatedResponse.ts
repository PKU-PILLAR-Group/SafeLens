import type { ExplorerRun } from "./types";

const SPECIAL_TOKEN_BOUNDARY = /<\|(?:im_start|im_end|endoftext|eot_id)\|>/i;
const NEXT_USER_TURN = /(?:\r?\n|([.!?。！？])\s+)(?:User|用户)\s*:(?=[\s\S]{0,4000}(?:Assistant|助手)\s*:)/i;

export function generatedResponseText(run: ExplorerRun): string {
  const generated = run.metadata?.generatedContinuation;
  if (typeof generated !== "string" || !generated.trim()) return "";

  const promptRunner = run.metadata?.promptRunner;
  const userPrompt = promptRunner && typeof promptRunner === "object" && !Array.isArray(promptRunner)
    ? (promptRunner as Record<string, unknown>).userPrompt
    : undefined;
  const prefixes = [run.prompt, typeof userPrompt === "string" ? userPrompt : ""]
    .filter(Boolean)
    .sort((left, right) => right.length - left.length);
  let response = generated.trim();
  const prefix = prefixes.find((candidate) => response.startsWith(candidate));
  if (prefix) response = response.slice(prefix.length).trim();
  response = response.replace(/^(?:Assistant|助手)\s*:\s*/i, "");
  return trimGeneratedTurn(response);
}

export function trimGeneratedTurn(value: string): string {
  let response = value.trim();
  const specialBoundary = response.search(SPECIAL_TOKEN_BOUNDARY);
  if (specialBoundary >= 0) response = response.slice(0, specialBoundary);
  const nextTurn = NEXT_USER_TURN.exec(response);
  if (nextTurn?.index !== undefined) {
    response = response.slice(0, nextTurn.index + (nextTurn[1]?.length ?? 0));
  }
  return response.trim();
}
