import { useEffect, useMemo, useState } from "react";

interface ResponseTokenPickerProps {
  response: string;
  selectedIndex: number;
  disabled?: boolean;
  onSelect: (index: number) => void;
}

const TOKEN_SPLIT = /(\s+|[A-Za-z0-9_]+|[^\sA-Za-z0-9_])/g;

export function ResponseTokenPicker({
  response,
  selectedIndex,
  disabled = false,
  onSelect
}: ResponseTokenPickerProps) {
  const [draft, setDraft] = useState(response);

  useEffect(() => {
    const timer = window.setTimeout(() => setDraft(response), 150);
    return () => window.clearTimeout(timer);
  }, [response]);

  const tokens = useMemo(() => tokenize(draft), [draft]);

  useEffect(() => {
    if (tokens.length > 0 && selectedIndex >= tokens.length) {
      onSelect(tokens.length - 1);
    }
  }, [onSelect, selectedIndex, tokens.length]);

  return (
    <div className="response-token-picker" aria-label="Attribution target token">
      <header>
        <span>Target token</span>
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
      {tokens.length > 0 ? (
        <div className="response-token-picker-list" role="group" aria-label="Response tokens">
          {tokens.map((token, index) => (
            <button
              key={`${index}:${token}`}
              type="button"
              className={index === selectedIndex ? "active" : ""}
              aria-pressed={index === selectedIndex}
              disabled={disabled}
              title={`Target token ${index} · ${token}`}
              onClick={() => onSelect(index)}
            >
              {token}
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

function tokenize(text: string): string[] {
  if (!text.trim()) return [];
  return text.split(TOKEN_SPLIT).filter((part) => part.length > 0 && !/^\s+$/.test(part));
}
