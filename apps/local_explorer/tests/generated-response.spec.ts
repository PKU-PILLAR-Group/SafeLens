import { expect, test } from "@playwright/test";

import { generatedResponseText } from "../src/generatedResponse";
import { realRun } from "../src/realRunData";

test("preserves a continuation that starts with the user prompt", () => {
  const run = {
    ...realRun,
    prompt: "Hello",
    metadata: {
      ...realRun.metadata,
      generatedContinuation: "Hello! How can I assist you today?",
      generation: {
        outputFormat: "continuation_only",
        generatedTokenCount: 10
      },
      promptRunner: {
        userPrompt: "Hello"
      }
    }
  };

  expect(generatedResponseText(run)).toBe("Hello! How can I assist you today?");
});

test("still removes the prompt prefix from legacy full-sequence output", () => {
  const prompt = "Why does the model focus on this token?";
  const run = {
    ...realRun,
    prompt,
    metadata: {
      ...realRun.metadata,
      generatedContinuation: `${prompt} The selected token carries the strongest alignment.`,
      promptRunner: {
        userPrompt: prompt
      }
    }
  };

  expect(generatedResponseText(run)).toBe("The selected token carries the strongest alignment.");
});
