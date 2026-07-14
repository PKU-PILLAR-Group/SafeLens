import { useId, useMemo, useRef, useState } from "react";
import { Check, ChevronDown, Search } from "lucide-react";

import type { RunRecord } from "../state/useRunLibrary";

export const VIRTUAL_RUN_SELECTOR_THRESHOLD = 100;
const VIRTUAL_OPTION_WINDOW = 8;

interface AdaptiveRunSelectorProps {
  records: RunRecord[];
  value: string;
  ariaLabel: string;
  onChange: (key: string) => void;
  formatNativeLabel?: (record: RunRecord) => string;
  className?: string;
}

export function AdaptiveRunSelector({
  records,
  value,
  ariaLabel,
  onChange,
  formatNativeLabel = (record) => `${record.runId} / ${record.sampleId}`,
  className
}: AdaptiveRunSelectorProps) {
  if (records.length <= VIRTUAL_RUN_SELECTOR_THRESHOLD) {
    return (
      <select
        className={className}
        aria-label={ariaLabel}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        {records.map((record) => (
          <option key={record.key} value={record.key}>{formatNativeLabel(record)}</option>
        ))}
      </select>
    );
  }
  return (
    <VirtualRunCombobox
      records={records}
      value={value}
      ariaLabel={ariaLabel}
      onChange={onChange}
      className={className}
    />
  );
}

function VirtualRunCombobox({
  records,
  value,
  ariaLabel,
  onChange,
  className
}: Omit<AdaptiveRunSelectorProps, "formatNativeLabel">) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [highlighted, setHighlighted] = useState(0);
  const rootRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listId = useId();
  const selected = records.find((record) => record.key === value) ?? records[0];
  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return records;
    return records.filter((record) => [
      record.runId,
      record.sampleId,
      record.modelName,
      record.sourceName,
      record.sourceType
    ].some((field) => field.toLowerCase().includes(normalized)));
  }, [query, records]);
  const safeHighlighted = Math.min(highlighted, Math.max(0, filtered.length - 1));
  const windowStart = Math.max(
    0,
    Math.min(
      safeHighlighted - Math.floor(VIRTUAL_OPTION_WINDOW / 2),
      filtered.length - VIRTUAL_OPTION_WINDOW
    )
  );
  const visible = filtered.slice(windowStart, windowStart + VIRTUAL_OPTION_WINDOW);
  const highlightedRecord = filtered[safeHighlighted];
  const activeDescendant = open && highlightedRecord
    ? `${listId}-option-${safeHighlighted}`
    : undefined;

  function openSelector() {
    setOpen(true);
    setQuery("");
    const selectedIndex = records.findIndex((record) => record.key === value);
    setHighlighted(Math.max(0, selectedIndex));
  }

  function choose(record: RunRecord) {
    onChange(record.key);
    setOpen(false);
    setQuery("");
  }

  function moveHighlight(next: number) {
    if (filtered.length === 0) return;
    setHighlighted(Math.max(0, Math.min(filtered.length - 1, next)));
  }

  return (
    <div
      ref={rootRef}
      className={`adaptive-run-selector ${className ?? ""}`}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setOpen(false);
      }}
    >
      <input
        ref={inputRef}
        role="combobox"
        aria-label={ariaLabel}
        aria-expanded={open}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-activedescendant={activeDescendant}
        value={open ? query : selected ? `${selected.runId} / ${selected.sampleId}` : ""}
        placeholder="Search runs"
        onFocus={(event) => {
          openSelector();
          window.requestAnimationFrame(() => event.currentTarget.select());
        }}
        onClick={() => {
          if (!open) openSelector();
        }}
        onChange={(event) => {
          if (!open) setOpen(true);
          setQuery(event.target.value);
          setHighlighted(0);
        }}
        onKeyDown={(event) => {
          if (event.key === "Escape") {
            event.preventDefault();
            setOpen(false);
            setQuery("");
            return;
          }
          if (!open && ["ArrowDown", "ArrowUp", "Enter"].includes(event.key)) {
            event.preventDefault();
            openSelector();
            return;
          }
          if (!open) return;
          if (event.key === "ArrowDown") {
            event.preventDefault();
            moveHighlight(safeHighlighted + 1);
          } else if (event.key === "ArrowUp") {
            event.preventDefault();
            moveHighlight(safeHighlighted - 1);
          } else if (event.key === "Home") {
            event.preventDefault();
            moveHighlight(0);
          } else if (event.key === "End") {
            event.preventDefault();
            moveHighlight(filtered.length - 1);
          } else if (event.key === "Enter" && highlightedRecord) {
            event.preventDefault();
            choose(highlightedRecord);
          }
        }}
      />
      <ChevronDown className="adaptive-run-chevron" size={14} aria-hidden="true" />

      {open && (
        <div className="adaptive-run-popup">
          <div className="adaptive-run-search-status">
            <Search size={12} />
            <span>{filtered.length} matching runs</span>
          </div>
          <div id={listId} className="adaptive-run-listbox" role="listbox" aria-label={`${ariaLabel} results`}>
            {visible.length > 0 ? visible.map((record, index) => {
              const absoluteIndex = windowStart + index;
              const selectedOption = record.key === value;
              return (
                <button
                  key={record.key}
                  id={`${listId}-option-${absoluteIndex}`}
                  type="button"
                  role="option"
                  aria-selected={selectedOption}
                  className={absoluteIndex === safeHighlighted ? "highlighted" : ""}
                  onMouseEnter={() => setHighlighted(absoluteIndex)}
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => choose(record)}
                >
                  <span><strong>{record.runId}</strong><em>{record.sourceType}</em></span>
                  <span>{record.sampleId} · {record.modelName}</span>
                  {selectedOption && <Check size={13} aria-hidden="true" />}
                </button>
              );
            }) : (
              <div className="adaptive-run-no-results" role="status">No matching runs.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
