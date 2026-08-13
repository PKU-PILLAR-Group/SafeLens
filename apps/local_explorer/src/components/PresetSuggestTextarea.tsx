import { useEffect, useId, useMemo, useRef, useState } from "react";
import { Plus, X } from "lucide-react";

import {
  createUserPreset,
  BUILTIN_PRESETS,
  loadUserPresets,
  matchPresets,
  presetsInCategory,
  saveUserPresets,
  STEERING_CATEGORIES,
  type SteeringCategory,
  type SteeringPreset
} from "../state/steeringPresets";

interface PresetSuggestTextareaProps {
  ariaLabel: string;
  label: string;
  value: string;
  direction: "toward" | "away";
  contextQuery?: string;
  disabled?: boolean;
  onChange: (value: string) => void;
  onSelectPreset?: (preset: SteeringPreset) => void;
}

export function PresetSuggestTextarea({
  ariaLabel,
  label,
  value,
  direction,
  contextQuery = "",
  disabled = false,
  onChange,
  onSelectPreset
}: PresetSuggestTextareaProps) {
  const [open, setOpen] = useState(false);
  const [highlighted, setHighlighted] = useState(0);
  const [userPresets, setUserPresets] = useState<SteeringPreset[]>(loadUserPresets);
  const [saveOpen, setSaveOpen] = useState(false);
  const [saveLabel, setSaveLabel] = useState("");
  const [category, setCategory] = useState<SteeringCategory>("safety");
  const rootRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const listId = useId();

  const matches = useMemo(
    () => matchPresets(value, direction, userPresets, contextQuery),
    [contextQuery, direction, userPresets, value]
  );
  const safeHighlighted = Math.min(highlighted, Math.max(0, matches.length - 1));
  const highlightedPreset = matches[safeHighlighted];
  const activeDescendant = open && highlightedPreset
    ? `${listId}-option-${safeHighlighted}`
    : undefined;
  const categoryPresets = useMemo(
    () => presetsInCategory(direction, category, userPresets),
    [category, direction, userPresets]
  );

  useEffect(() => {
    const selected = [...userPresets, ...BUILTIN_PRESETS].find(
      (preset) => preset.direction === direction && preset.text === value && preset.category
    );
    if (selected?.category) setCategory(selected.category);
  }, [direction, userPresets, value]);

  function choose(preset: SteeringPreset) {
    if (onSelectPreset) onSelectPreset(preset);
    else onChange(preset.text);
    setOpen(false);
    setHighlighted(0);
    window.requestAnimationFrame(() => textareaRef.current?.focus());
  }

  function removeUserPreset(id: string) {
    const next = userPresets.filter((preset) => preset.id !== id);
    setUserPresets(next);
    saveUserPresets(next);
  }

  function saveCurrent() {
    const label = saveLabel.trim();
    if (!label || !value.trim()) return;
    const next = [...userPresets, createUserPreset(label, value, direction, category)];
    setUserPresets(next);
    saveUserPresets(next);
    setSaveLabel("");
    setSaveOpen(false);
  }

  return (
    <div
      ref={rootRef}
      className="preset-suggest"
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
          setOpen(false);
          setSaveOpen(false);
        }
      }}
    >
      <span>
        {label}
        <button
          type="button"
          className="preset-suggest-save"
          aria-label={`Save current ${label} text as a preset`}
          disabled={disabled || !value.trim()}
          onClick={() => setSaveOpen((current) => !current)}
        >
          <Plus size={12} /> Save as preset
        </button>
      </span>
      <div className="preset-suggest-categories" role="group" aria-label={`${label} category`}>
        {STEERING_CATEGORIES.map((item) => (
          <button
            key={item.id}
            type="button"
            className={category === item.id ? "active" : ""}
            aria-pressed={category === item.id}
            disabled={disabled}
            onClick={() => setCategory(item.id)}
          >{item.label}</button>
        ))}
        <select
          aria-label={`${label} direction preset`}
          value=""
          disabled={disabled}
          onChange={(event) => {
            const preset = categoryPresets.find((item) => item.id === event.target.value);
            if (preset) choose(preset);
          }}
        >
          <option value="">Choose direction...</option>
          {categoryPresets.map((preset) => <option key={preset.id} value={preset.id}>{preset.label}</option>)}
        </select>
      </div>
      <textarea
        ref={textareaRef}
        aria-label={ariaLabel}
        rows={3}
        value={value}
        disabled={disabled}
        role="combobox"
        aria-expanded={open}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-activedescendant={activeDescendant}
        onFocus={() => setOpen(true)}
        onChange={(event) => {
          onChange(event.target.value);
          if (!open) setOpen(true);
          setHighlighted(0);
        }}
        onKeyDown={(event) => {
          if (event.key === "Escape") {
            if (open) {
              event.preventDefault();
              setOpen(false);
            }
            return;
          }
          if (!open) return;
          if (event.key === "ArrowDown") {
            event.preventDefault();
            setHighlighted(Math.min(matches.length - 1, safeHighlighted + 1));
          } else if (event.key === "ArrowUp") {
            event.preventDefault();
            setHighlighted(Math.max(0, safeHighlighted - 1));
          } else if (event.key === "Home") {
            event.preventDefault();
            setHighlighted(0);
          } else if (event.key === "End") {
            event.preventDefault();
            setHighlighted(Math.max(0, matches.length - 1));
          } else if (event.key === "Enter" && highlightedPreset) {
            event.preventDefault();
            choose(highlightedPreset);
          }
        }}
      />
      {matches.length > 0 && (
        <div className="preset-suggest-chips" aria-label={`${label} suggested presets`}>
          {matches.slice(0, 3).map((preset) => (
            <button
              key={`chip-${preset.id}`}
              type="button"
              disabled={disabled}
              title={preset.text}
              onClick={() => choose(preset)}
            >{preset.label}</button>
          ))}
        </div>
      )}
      {saveOpen && (
        <div className="preset-suggest-save-form" role="group" aria-label={`Save ${label} preset`}>
          <input
            aria-label="Preset label"
            placeholder="Preset label"
            value={saveLabel}
            onChange={(event) => setSaveLabel(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                saveCurrent();
              }
            }}
          />
          <button type="button" onClick={saveCurrent} disabled={!saveLabel.trim()}>
            Save
          </button>
        </div>
      )}
      {open && matches.length > 0 && (
        <div
          id={listId}
          className="preset-suggest-list"
          role="listbox"
          aria-label={`${label} preset suggestions`}
        >
          {matches.map((preset, index) => (
            <button
              key={preset.id}
              id={`${listId}-option-${index}`}
              type="button"
              role="option"
              aria-selected={index === safeHighlighted}
              className={`preset-suggest-item ${index === safeHighlighted ? "highlighted" : ""}`}
              data-source={preset.source}
              onMouseEnter={() => setHighlighted(index)}
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => choose(preset)}
            >
              <strong>{preset.label}</strong>
              <em>{preset.source === "user" ? "custom" : "builtin"}</em>
              <small>{preset.text}</small>
              {preset.source === "user" && (
                <span
                  role="button"
                  aria-label={`Delete preset ${preset.label}`}
                  className="preset-suggest-delete"
                  onClick={(event) => {
                    event.stopPropagation();
                    removeUserPreset(preset.id);
                  }}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      event.stopPropagation();
                      removeUserPreset(preset.id);
                    }
                  }}
                >
                  <X size={12} />
                </span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
