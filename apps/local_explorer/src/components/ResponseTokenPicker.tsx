import { useEffect, useState } from "react";

import { fetchTokenizedResponse, type TokenizedResponse } from "../api/explorerClient";

interface ResponseTokenPickerProps {
  modelName: string;
  response: string;
  selectedIndex: number;
  disabled?: boolean;
  onSelect: (index: number) => void;
  onTokensChange?: (tokens: TokenizedResponse["tokens"]) => void;
}

export function ResponseTokenPicker({
  modelName,
  response,
  selectedIndex,
  disabled = false,
  onSelect,
  onTokensChange
}: ResponseTokenPickerProps) {
  const [tokens, setTokens] = useState<TokenizedResponse["tokens"]>([]);
  const [status, setStatus] = useState<"idle" | "loading" | "ready" | "error">("idle");

  useEffect(() => {
    const cleaned = response.trim();
    if (!cleaned) {
      setTokens([]);
      onTokensChange?.([]);
      setStatus("idle");
      return;
    }
    setTokens([]);
    onTokensChange?.([]);
    setStatus("loading");
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      void fetchTokenizedResponse(modelName, response, controller.signal)
        .then((result) => {
          setTokens(result.tokens);
          onTokensChange?.(result.tokens);
          setStatus("ready");
        })
        .catch(() => {
          if (!controller.signal.aborted) {
            setTokens([]);
            onTokensChange?.([]);
            setStatus("error");
          }
        });
    }, 180);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [modelName, onTokensChange, response]);

  useEffect(() => {
    if (tokens.length > 0 && selectedIndex >= tokens.length) {
      onSelect(tokens.length - 1);
    }
  }, [onSelect, selectedIndex, tokens.length]);

  return (
    <div className="response-token-picker" aria-label="Attribution target token" aria-busy={status === "loading"}>
      <header>
        <span>Target response token</span>
        {tokens.length > 0 && (
          <button
            type="button"
            disabled={disabled}
            onClick={() => onSelect(0)}
          >
            Reset to first
          </button>
        )}
      </header>
      {status === "loading" ? (
        <div className="response-token-picker-empty" role="status">Tokenizing response...</div>
      ) : status === "error" ? (
        <div className="response-token-picker-empty is-error" role="status">Tokenizer unavailable. Check the local model worker.</div>
      ) : tokens.length > 0 ? (
        <div className="response-token-picker-list" role="group" aria-label="Response tokens">
          {tokens.map((token, index) => (
            <button
              key={`${index}:${token.tokenId}`}
              type="button"
              className={index === selectedIndex ? "active" : ""}
              aria-pressed={index === selectedIndex}
              disabled={disabled}
              title={`Target token ${index} · ${token.text || "space"} · ID ${token.tokenId}`}
              onClick={() => onSelect(index)}
            >
              {token.text || "space"}
              <sub>T{index}</sub>
            </button>
          ))}
        </div>
      ) : (
        <div className="response-token-picker-empty" role="status">
          Type or paste the model response to pick a target token.
        </div>
      )}
    </div>
  );
}
