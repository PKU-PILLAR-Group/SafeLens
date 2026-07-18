import React, { useEffect } from "react";
import {
  Activity,
  BarChart3,
  BrainCircuit,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  FlaskConical,
  GitCompareArrows,
  Info,
  Layers3,
  MessageSquareText,
  Network,
  PanelRightOpen,
  Pin,
  SlidersHorizontal,
  Sparkles,
  Waves,
  X
} from "lucide-react";

import type { WorkspaceView } from "../types";

export function LayerSelector({
  layers,
  selectedLayer,
  onSelect
}: {
  layers: number[];
  selectedLayer: number;
  onSelect: (layer: number) => void;
}) {
  return (
    <div className="layer-picker main-layer-picker" role="group" aria-label="Layer selector">
      <span className="control-label">Layer</span>
      {layers.length <= 16 ? (
        <div className="layer-button-selector" role="radiogroup" aria-label="Analysis layer">
          {layers.map((layer) => (
            <button
              key={layer}
              role="radio"
              data-layer={layer}
              aria-checked={selectedLayer === layer}
              tabIndex={selectedLayer === layer ? 0 : -1}
              className={selectedLayer === layer ? "active" : ""}
              onClick={() => onSelect(layer)}
              onKeyDown={(event) => handleLayerKeyDown(event, layers, layer, onSelect)}
            >
              L{layer}
            </button>
          ))}
        </div>
      ) : (
        <CompactLayerSelector
          layers={layers}
          selectedLayer={selectedLayer}
          onSelect={onSelect}
        />
      )}
    </div>
  );
}

export function SelectionWorkbench({
  visible,
  tokenText,
  tokenIndex,
  layer,
  score,
  view,
  menuOpen,
  contextOpen,
  pinned,
  canPin,
  pinnedCount,
  onToggleMenu,
  onSelectView,
  onInspect,
  onToggleContext,
  onPin,
  onPreloadCompare,
  onCompare,
  onDismiss
}: {
  visible: boolean;
  tokenText: string;
  tokenIndex: number;
  layer: number;
  score: string;
  view: WorkspaceView;
  menuOpen: boolean;
  contextOpen: boolean;
  pinned: boolean;
  canPin: boolean;
  pinnedCount: number;
  onToggleMenu: () => void;
  onSelectView: (view: WorkspaceView) => void;
  onInspect: (trigger: HTMLButtonElement) => void;
  onToggleContext: () => void;
  onPin: () => void;
  onPreloadCompare: () => void;
  onCompare: (trigger: HTMLButtonElement) => void;
  onDismiss: () => void;
}) {
  const workbenchRef = React.useRef<HTMLElement>(null);

  useEffect(() => {
    if (!menuOpen) return;
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key !== "Escape") return;
      event.preventDefault();
      onToggleMenu();
    }
    function closeOnOutsidePointer(event: PointerEvent) {
      if (workbenchRef.current?.contains(event.target as Node)) return;
      onToggleMenu();
    }
    window.addEventListener("keydown", closeOnEscape);
    window.addEventListener("pointerdown", closeOnOutsidePointer);
    return () => {
      window.removeEventListener("keydown", closeOnEscape);
      window.removeEventListener("pointerdown", closeOnOutsidePointer);
    };
  }, [menuOpen, onToggleMenu]);

  if (!visible) return null;

  const methods: Array<{
    id: WorkspaceView;
    label: string;
    icon: React.ReactNode;
  }> = [
    { id: "overview", label: "Overview", icon: <Activity size={16} /> },
    { id: "residual", label: "Residual", icon: <Waves size={16} /> },
    { id: "attention", label: "Attention", icon: <Network size={16} /> },
    { id: "mlp", label: "MLP", icon: <BrainCircuit size={16} /> },
    { id: "nla", label: "NLA", icon: <Sparkles size={16} /> },
    { id: "attribution", label: "Attribution", icon: <BarChart3 size={16} /> },
    { id: "patching", label: "Patching", icon: <FlaskConical size={16} /> },
    {
      id: "intervention",
      label: "Intervention",
      icon: <SlidersHorizontal size={16} />
    }
  ];
  const visibleText = tokenText.trim() || "space";

  return (
    <section
      ref={workbenchRef}
      className="selection-workbench"
      aria-label="Selected token actions"
      aria-live="polite"
    >
      <div className="selection-workbench-main">
        <div className="selection-workbench-identity">
          <span aria-hidden="true" />
          <div>
            <small>Selected token</small>
            <strong>{visibleText}</strong>
          </div>
          <dl>
            <div><dt>Position</dt><dd>T{tokenIndex}</dd></div>
            <div><dt>Layer</dt><dd>L{layer}</dd></div>
            <div><dt>Safety proxy</dt><dd>{score}</dd></div>
          </dl>
        </div>
        <div className="selection-workbench-actions">
          <button
            className={menuOpen ? "active" : ""}
            aria-expanded={menuOpen}
            aria-haspopup="menu"
            aria-controls="selection-analysis-menu"
            title="Choose an analysis for the selected token"
            onClick={onToggleMenu}
          >
            <Sparkles size={16} /> Analyze
          </button>
          <button title="Inspect selected evidence" onClick={(event) => onInspect(event.currentTarget)}>
            <Info size={16} /> Inspect
          </button>
          <button
            className={contextOpen ? "active" : ""}
            aria-expanded={contextOpen}
            title="Toggle supporting context"
            onClick={onToggleContext}
          >
            <PanelRightOpen size={16} /> Context
          </button>
          <button
            className={pinned ? "active" : ""}
            aria-pressed={pinned}
            disabled={!canPin}
            title={pinned ? "Unpin selected evidence" : "Pin selected evidence"}
            onClick={onPin}
          >
            <Pin size={16} /> {pinned ? "Unpin" : "Pin"}
          </button>
          <button
            disabled={!pinnedCount}
            title="Compare pinned evidence"
            onPointerEnter={onPreloadCompare}
            onFocus={onPreloadCompare}
            onClick={(event) => onCompare(event.currentTarget)}
          >
            <GitCompareArrows size={16} /> Compare
            <b>{pinnedCount}</b>
          </button>
          <button
            className="selection-workbench-dismiss"
            aria-label="Dismiss selected token actions"
            onClick={onDismiss}
          >
            <X size={16} />
          </button>
        </div>
      </div>

      {menuOpen && (
        <div
          id="selection-analysis-menu"
          className="selection-analysis-menu"
          role="menu"
          aria-label="Analyze selected token"
        >
          {methods.map((method) => (
            <button
              key={method.id}
              role="menuitemradio"
              aria-checked={view === method.id}
              className={view === method.id ? "active" : ""}
              onClick={() => onSelectView(method.id)}
            >
              {method.icon}
              <span>{method.label}</span>
              {view === method.id && <CheckCircle2 size={14} />}
            </button>
          ))}
        </div>
      )}
    </section>
  );
}

export function WorkspaceTabs({
  view,
  setView
}: {
  view: WorkspaceView;
  setView: (view: WorkspaceView) => void;
}) {
  const tabListRef = React.useRef<HTMLDivElement>(null);
  const tabScrollDirectionRef = React.useRef<-1 | 1 | null>(null);
  const [scrollState, setScrollState] = React.useState({ previous: false, next: false });
  const views: Array<{ id: WorkspaceView; label: string; icon: React.ReactNode }> = [
    { id: "overview", label: "Overview", icon: <Activity size={15} /> },
    { id: "residual", label: "Residual", icon: <Waves size={15} /> },
    { id: "attention", label: "Attention", icon: <Network size={15} /> },
    { id: "mlp", label: "MLP", icon: <Layers3 size={15} /> },
    { id: "nla", label: "NLA", icon: <MessageSquareText size={15} /> },
    { id: "patching", label: "Patching", icon: <FlaskConical size={15} /> },
    { id: "intervention", label: "Intervention", icon: <SlidersHorizontal size={15} /> },
    { id: "attribution", label: "Attribution", icon: <BarChart3 size={15} /> }
  ];

  useEffect(() => {
    const tabList = tabListRef.current;
    if (!tabList || !window.matchMedia("(max-width: 860px)").matches) return;
    const tabs = [...tabList.querySelectorAll<HTMLElement>('[role="tab"]')];
    const selectedIndex = tabs.findIndex((tab) => tab.id === `analysis-tab-${view}`);
    const first = tabs[0];
    if (selectedIndex < 0 || !first) return;
    const gap = Number.parseFloat(getComputedStyle(tabList).columnGap) || 6;
    const pageSize = Math.max(
      1,
      Math.floor((tabList.clientWidth + gap) / Math.max(1, first.offsetWidth + gap))
    );
    const pageStart = Math.floor(selectedIndex / pageSize) * pageSize;
    tabList.scrollLeft = Math.max(
      0,
      (tabs[pageStart]?.offsetLeft ?? first.offsetLeft) - first.offsetLeft
    );
    window.requestAnimationFrame(() => updateTabScrollState(tabList, setScrollState));
  }, [view]);

  useEffect(() => {
    const tabList = tabListRef.current;
    if (!tabList) return;
    const update = () => updateTabScrollState(tabList, setScrollState);
    const observer = new ResizeObserver(update);
    tabList.addEventListener("scroll", update, { passive: true });
    observer.observe(tabList);
    window.requestAnimationFrame(update);
    return () => {
      tabList.removeEventListener("scroll", update);
      observer.disconnect();
    };
  }, []);

  useEffect(() => {
    const direction = tabScrollDirectionRef.current;
    const tabList = tabListRef.current;
    if (!direction || !tabList) return;
    if (direction === 1 && !scrollState.next) {
      tabScrollDirectionRef.current = null;
      tabList.querySelectorAll<HTMLButtonElement>('[role="tab"]')
        .item(views.length - 1)
        .focus({ preventScroll: true });
    }
    if (direction === -1 && !scrollState.previous) {
      tabScrollDirectionRef.current = null;
      tabList.querySelector<HTMLButtonElement>('[role="tab"]')?.focus({ preventScroll: true });
    }
  }, [scrollState.next, scrollState.previous, views.length]);

  function scrollTabs(direction: -1 | 1) {
    const tabList = tabListRef.current;
    if (!tabList) return;
    tabScrollDirectionRef.current = direction;
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    tabList.scrollBy({
      left: direction * tabList.clientWidth,
      behavior: reduceMotion ? "auto" : "smooth"
    });
  }

  function selectFromKeyboard(event: React.KeyboardEvent<HTMLButtonElement>, index: number) {
    let nextIndex: number | undefined;
    if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
      nextIndex = (index - 1 + views.length) % views.length;
    } else if (event.key === "ArrowRight" || event.key === "ArrowDown") {
      nextIndex = (index + 1) % views.length;
    } else if (event.key === "Home") {
      nextIndex = 0;
    } else if (event.key === "End") {
      nextIndex = views.length - 1;
    }
    if (nextIndex === undefined) return;
    event.preventDefault();
    const next = views[nextIndex];
    setView(next.id);
    event.currentTarget.parentElement
      ?.querySelector<HTMLButtonElement>(`#analysis-tab-${next.id}`)
      ?.focus();
  }

  return (
    <div
      className={`workspace-tabs-shell ${scrollState.previous ? "has-previous" : ""} ${scrollState.next ? "has-next" : ""}`}
    >
      <button
        type="button"
        className="workspace-tabs-scroll previous"
        aria-label="Show previous analysis views"
        aria-controls="analysis-view-tabs"
        title={scrollState.previous ? "Previous views" : "At first view page"}
        disabled={!scrollState.previous}
        onClick={() => scrollTabs(-1)}
      >
        <ChevronLeft size={17} />
      </button>
      <div
        ref={tabListRef}
        id="analysis-view-tabs"
        className="workspace-tabs"
        role="tablist"
        aria-label="Analysis view"
      >
        {views.map((item, index) => (
          <button
            key={item.id}
            id={`analysis-tab-${item.id}`}
            role="tab"
            aria-controls="analysis-panel"
            aria-selected={view === item.id}
            tabIndex={view === item.id ? 0 : -1}
            className={view === item.id ? "active" : ""}
            onClick={() => setView(item.id)}
            onKeyDown={(event) => selectFromKeyboard(event, index)}
          >
            {item.icon}
            <span>{item.label}</span>
          </button>
        ))}
      </div>
      <button
        type="button"
        className="workspace-tabs-scroll next"
        aria-label="Show more analysis views"
        aria-controls="analysis-view-tabs"
        title={scrollState.next ? "More views" : "At last view page"}
        disabled={!scrollState.next}
        onClick={() => scrollTabs(1)}
      >
        <ChevronRight size={17} />
      </button>
    </div>
  );
}

function updateTabScrollState(
  tabList: HTMLDivElement,
  setState: React.Dispatch<React.SetStateAction<{ previous: boolean; next: boolean }>>
) {
  const maximum = Math.max(0, tabList.scrollWidth - tabList.clientWidth);
  const next = {
    previous: tabList.scrollLeft > 2,
    next: tabList.scrollLeft < maximum - 2
  };
  setState((current) =>
    current.previous === next.previous && current.next === next.next ? current : next
  );
}

function handleLayerKeyDown(
  event: React.KeyboardEvent<HTMLButtonElement>,
  layers: number[],
  layer: number,
  onSelect: (layer: number) => void
) {
  const currentIndex = layers.indexOf(layer);
  let nextIndex: number | undefined;
  if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
    nextIndex = (currentIndex - 1 + layers.length) % layers.length;
  } else if (event.key === "ArrowRight" || event.key === "ArrowDown") {
    nextIndex = (currentIndex + 1) % layers.length;
  } else if (event.key === "Home") {
    nextIndex = 0;
  } else if (event.key === "End") {
    nextIndex = layers.length - 1;
  }
  if (nextIndex === undefined) return;
  event.preventDefault();
  const nextLayer = layers[nextIndex];
  onSelect(nextLayer);
  event.currentTarget.parentElement
    ?.querySelector<HTMLButtonElement>(`[role="radio"][data-layer="${nextLayer}"]`)
    ?.focus();
}

function CompactLayerSelector({
  layers,
  selectedLayer,
  onSelect
}: {
  layers: number[];
  selectedLayer: number;
  onSelect: (layer: number) => void;
}) {
  const selectedIndex = Math.max(0, layers.indexOf(selectedLayer));
  return (
    <div className="compact-layer-selector">
      <button
        aria-label="Previous layer"
        title="Previous layer"
        disabled={selectedIndex === 0}
        onClick={() => onSelect(layers[selectedIndex - 1])}
      >
        <ChevronLeft size={14} />
      </button>
      <select
        aria-label="Selected layer"
        value={layers[selectedIndex]}
        onChange={(event) => onSelect(Number(event.target.value))}
      >
        {layers.map((layer) => <option key={layer} value={layer}>Layer {layer}</option>)}
      </select>
      <button
        aria-label="Next layer"
        title="Next layer"
        disabled={selectedIndex >= layers.length - 1}
        onClick={() => onSelect(layers[selectedIndex + 1])}
      >
        <ChevronRight size={14} />
      </button>
      <span>{selectedIndex + 1} / {layers.length}</span>
    </div>
  );
}
