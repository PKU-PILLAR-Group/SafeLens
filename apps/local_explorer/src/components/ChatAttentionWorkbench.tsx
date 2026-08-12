import { useEffect, useMemo, useRef, useState } from "react";
import { Activity, ArrowDown, ArrowRight, Network } from "lucide-react";

import type { AttentionHead, ExplorerRun, TokenInfo } from "../types";

interface ChatAttentionWorkbenchProps {
  run: ExplorerRun;
}

const MAX_CHAT_ATTENTION_TOKENS = 160;

export function ChatAttentionWorkbench({ run }: ChatAttentionWorkbenchProps) {
  const rawHeads = useMemo(
    () => run.attentionHeads.filter((head) => !head.aggregation && !head.difference && !head.rollout),
    [run.attentionHeads]
  );
  const availableLayers = useMemo(
    () => [...new Set(rawHeads.map((head) => head.layer))].sort((left, right) => left - right),
    [rawHeads]
  );
  const initialLayer = availableLayers[availableLayers.length - 1] ?? run.layers[run.layers.length - 1] ?? 0;
  const [selectedLayer, setSelectedLayer] = useState(initialLayer);
  const layerHeads = rawHeads.filter((head) => head.layer === selectedLayer);
  const [selectedHeadId, setSelectedHeadId] = useState(layerHeads[0]?.id ?? rawHeads[0]?.id ?? "");
  const selectedHead = layerHeads.find((head) => head.id === selectedHeadId) ?? layerHeads[0] ?? rawHeads[0];
  const tokens = run.tokens;
  const [selectedDestination, setSelectedDestination] = useState(tokens[tokens.length - 1]?.index ?? 0);
  const [selectedSource, setSelectedSource] = useState(0);

  useEffect(() => {
    const nextHead = rawHeads.find((head) => head.layer === selectedLayer);
    if (nextHead && !layerHeads.some((head) => head.id === selectedHeadId)) setSelectedHeadId(nextHead.id);
  }, [layerHeads, rawHeads, selectedHeadId, selectedLayer]);

  useEffect(() => {
    if (!selectedHead) return;
    const destination = Math.min(selectedDestination, tokens[tokens.length - 1]?.index ?? 0);
    setSelectedDestination(destination);
    setSelectedSource(peakSource(selectedHead, destination));
  }, [selectedHead?.id]);

  if (!selectedHead) {
    return (
      <section className="chat-analysis-workbench chat-attention-workbench" aria-label="Attention heads workbench">
        <header className="chat-workbench-heading">
          <span><Network size={17} /></span><div><h2>Attention heads</h2><p>No attention-head matrix is cached for this run.</p></div>
        </header>
      </section>
    );
  }

  const selectedDestinationToken = tokens.find((token) => token.index === selectedDestination) ?? tokens[0];
  const incoming = incomingAttention(selectedHead, selectedDestination, tokens);
  const incomingMaximum = Math.max(1e-12, ...incoming.map((item) => item.value));
  const displayedTokens = tokens.slice(0, MAX_CHAT_ATTENTION_TOKENS);

  function selectLayer(layer: number) {
    setSelectedLayer(layer);
    const nextHead = rawHeads.find((head) => head.layer === layer);
    if (nextHead) setSelectedHeadId(nextHead.id);
  }

  function selectDestination(destination: number) {
    const next = Math.max(0, Math.min(tokens.length - 1, destination));
    setSelectedDestination(next);
    setSelectedSource(peakSource(selectedHead, next));
  }

  function selectPair(source: number, destination: number) {
    const nextDestination = Math.max(0, Math.min(tokens.length - 1, destination));
    const nextSource = Math.max(0, Math.min(nextDestination, source));
    setSelectedDestination(nextDestination);
    setSelectedSource(nextSource);
  }

  return (
    <section className="chat-analysis-workbench chat-attention-workbench" aria-label="Attention heads workbench">
      <header className="chat-workbench-heading">
        <span><Network size={17} /></span>
        <div><h2>Attention heads</h2><p>Compare raw head patterns and inspect one destination token</p></div>
        <span className="chat-workbench-status ready"><i />{rawHeads.length} heads</span>
      </header>

      <div className="chat-attention-controls">
        <label>
          <span>Layer</span>
          <select aria-label="Attention heads layer" value={selectedLayer} onChange={(event) => selectLayer(Number(event.target.value))}>
            {availableLayers.map((layer) => <option key={layer} value={layer}>Layer {layer}</option>)}
          </select>
        </label>
        <label>
          <span>Head</span>
          <select aria-label="Attention head" value={selectedHead.id} onChange={(event) => setSelectedHeadId(event.target.value)}>
            {layerHeads.map((head) => <option key={head.id} value={head.id}>{head.id} · {head.role}</option>)}
          </select>
        </label>
        <div className="chat-attention-focus" aria-label="Selected attention pair">
          <span><small>Destination</small><b>T{selectedDestination} · {visibleToken(selectedDestinationToken?.text ?? "")}</b></span>
          <ArrowRight size={15} />
          <span><small>Source</small><b>T{selectedSource} · {visibleToken(tokens[selectedSource]?.text ?? "")}</b></span>
        </div>
      </div>

      <section className="chat-head-overview" aria-label="Attention head overview">
        <header><div><strong>Heads at layer {selectedLayer}</strong><small>Select a head to compare its pattern</small></div><span>{layerHeads.length} raw distributions</span></header>
        <div role="radiogroup" aria-label="Attention head choices">
          {layerHeads.map((head) => (
            <button
              key={head.id}
              type="button"
              role="radio"
              aria-checked={head.id === selectedHead.id}
              className={head.id === selectedHead.id ? "active" : ""}
              onClick={() => setSelectedHeadId(head.id)}
            >
              <MiniHeadHeatmap head={head} tokens={tokens} />
              <span><b>{head.id}</b><small>{head.role}</small></span>
              <em>risk {head.riskContribution.toFixed(3)}</em>
            </button>
          ))}
        </div>
      </section>

      <div className="chat-attention-token-picker">
        <header><span><b>1</b> Choose destination token</span><small>{tokens.length} tokens · source must be at or before destination</small></header>
        <div role="radiogroup" aria-label="Attention destination token">
          {tokens.map((token) => (
            <button
              type="button"
              key={token.index}
              role="radio"
              aria-checked={selectedDestination === token.index}
              aria-label={`Destination token ${token.index} ${visibleToken(token.text)}`}
              className={selectedDestination === token.index ? "active" : ""}
              onClick={() => selectDestination(token.index)}
            ><small>{token.index}</small><span>{visibleToken(token.text)}</span></button>
          ))}
        </div>
      </div>

      <section className="chat-attention-detail" aria-label="Selected attention head detail">
        <header>
          <div><Activity size={16} /><strong>{selectedHead.id} · {selectedHead.role}</strong><small>Layer {selectedHead.layer} · head {selectedHead.head}</small></div>
          <div className="chat-attention-metrics"><span><b>{selectedHead.entropy.toFixed(3)}</b> entropy</span><span><b>{selectedHead.riskContribution.toFixed(3)}</b> risk proxy</span></div>
        </header>
        <div className="chat-attention-visuals">
          <div className="chat-attention-heatmap-wrap">
            <AttentionHeatmap
              head={selectedHead}
              tokens={displayedTokens}
              selectedSource={selectedSource}
              selectedDestination={selectedDestination}
              onSelectPair={selectPair}
            />
            {tokens.length > MAX_CHAT_ATTENTION_TOKENS && <p>Heatmap shows the first {MAX_CHAT_ATTENTION_TOKENS} tokens; the selected distribution below includes the full run.</p>}
          </div>
          <div className="chat-attention-incoming">
            <header><strong>Incoming attention</strong><small>Destination T{selectedDestination}</small></header>
            {incoming.slice().sort((left, right) => right.value - left.value).slice(0, 10).map((item) => (
              <button
                type="button"
                key={item.token.index}
                className={item.token.index === selectedSource ? "active" : ""}
                onClick={() => selectPair(item.token.index, selectedDestination)}
                aria-label={`Source token ${item.token.index} ${visibleToken(item.token.text)}, attention ${item.value.toFixed(6)}`}
              >
                <span><small>T{item.token.index}</small><b>{visibleToken(item.token.text)}</b></span>
                <i><span style={{ width: `${Math.max(3, item.value / incomingMaximum * 100)}%` }} /></i>
                <em>{item.value.toFixed(4)}</em>
              </button>
            ))}
          </div>
        </div>
      </section>
      <p className="chat-explanation-note">Values are raw softmax attention probabilities from the cached model forward pass. Masked future positions are not selectable.</p>
    </section>
  );
}

function MiniHeadHeatmap({ head, tokens }: { head: AttentionHead; tokens: TokenInfo[] }) {
  const positions = samplePositions(tokens.length, 8);
  return (
    <svg className="chat-mini-head-heatmap" viewBox="0 0 8 8" role="img" aria-label={`${head.id} attention mini heatmap`}>
      {positions.flatMap((destination, row) => positions.map((source, column) => {
        const value = source > destination ? 0 : head.distributionByToken[destination]?.[source] ?? 0;
        return <rect key={`${row}-${column}`} x={column} y={row} width="0.92" height="0.92" fill={source > destination ? "#edf0f0" : `rgba(36,139,120,${0.12 + Math.min(0.88, value * 5)})`} />;
      }))}
    </svg>
  );
}

function AttentionHeatmap({
  head,
  tokens,
  selectedSource,
  selectedDestination,
  onSelectPair
}: {
  head: AttentionHead;
  tokens: TokenInfo[];
  selectedSource: number;
  selectedDestination: number;
  onSelectPair: (source: number, destination: number) => void;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const selectedSourcePosition = tokens.findIndex((token) => token.index === selectedSource);
  const selectedDestinationPosition = tokens.findIndex((token) => token.index === selectedDestination);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || tokens.length === 0) return;
    const container = canvas.parentElement;
    if (!container) return;
    const draw = () => {
      const rect = container.getBoundingClientRect();
      const size = Math.max(1, Math.min(560, rect.width));
      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.round(size * dpr);
      canvas.height = Math.round(size * dpr);
      const context = canvas.getContext("2d");
      if (!context) return;
      context.setTransform(dpr, 0, 0, dpr, 0, 0);
      context.clearRect(0, 0, size, size);
      const cell = size / tokens.length;
      let maximum = 1e-12;
      for (const token of tokens) {
        for (const value of head.distributionByToken[token.index] ?? []) maximum = Math.max(maximum, value);
      }
      for (let row = 0; row < tokens.length; row += 1) {
        const destination = tokens[row].index;
        for (let column = 0; column < tokens.length; column += 1) {
          const source = tokens[column].index;
          if (source > destination) {
            context.fillStyle = "#eef1f1";
          } else {
            const value = head.distributionByToken[destination]?.[source] ?? 0;
            context.fillStyle = `rgba(36, 139, 120, ${0.08 + Math.min(0.92, value / maximum)})`;
          }
          context.fillRect(column * cell, row * cell, Math.ceil(cell), Math.ceil(cell));
        }
      }
      if (selectedDestinationPosition >= 0) {
        context.strokeStyle = "#c58a32";
        context.lineWidth = 2;
        context.strokeRect(0.5, selectedDestinationPosition * cell + 0.5, size - 1, cell - 1);
      }
      if (selectedSourcePosition >= 0 && selectedDestinationPosition >= 0 && selectedSourcePosition <= selectedDestinationPosition) {
        context.strokeStyle = "#1d4f48";
        context.lineWidth = 2;
        context.strokeRect(selectedSourcePosition * cell + 0.5, selectedDestinationPosition * cell + 0.5, Math.max(1, cell - 1), Math.max(1, cell - 1));
      }
    };
    draw();
    const observer = new ResizeObserver(draw);
    observer.observe(container);
    return () => observer.disconnect();
  }, [head, selectedDestinationPosition, selectedSourcePosition, tokens]);

  function selectFromPointer(event: React.PointerEvent<HTMLCanvasElement>) {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const row = Math.max(0, Math.min(tokens.length - 1, Math.floor((event.clientY - rect.top) / rect.height * tokens.length)));
    const column = Math.max(0, Math.min(tokens.length - 1, Math.floor((event.clientX - rect.left) / rect.width * tokens.length)));
    const destination = tokens[row]?.index;
    const source = tokens[column]?.index;
    if (destination !== undefined && source !== undefined && source <= destination) onSelectPair(source, destination);
  }

  function moveFocus(event: React.KeyboardEvent<HTMLCanvasElement>) {
    if (!["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    const row = Math.max(0, selectedDestinationPosition);
    let destination = row;
    let source = Math.max(0, selectedSourcePosition);
    if (event.key === "ArrowUp") destination = Math.max(0, row - 1);
    if (event.key === "ArrowDown") destination = Math.min(tokens.length - 1, row + 1);
    if (event.key === "ArrowLeft") source = Math.max(0, source - 1);
    if (event.key === "ArrowRight") source = Math.min(destination, source + 1);
    if (event.key === "Home") source = 0;
    if (event.key === "End") source = destination;
    onSelectPair(tokens[source]?.index ?? 0, tokens[destination]?.index ?? 0);
  }

  return (
    <div className="chat-attention-heatmap" aria-label="Attention head heatmap">
      <canvas
        ref={canvasRef}
        role="img"
        tabIndex={0}
        aria-label={`${head.id} attention heatmap, destination ${selectedDestination}, source ${selectedSource}`}
        onPointerDown={selectFromPointer}
        onKeyDown={moveFocus}
      />
      <div className="chat-attention-heatmap-labels"><span>destination ↓</span><span>source →</span></div>
    </div>
  );
}

function incomingAttention(head: AttentionHead, destination: number, tokens: TokenInfo[]) {
  return tokens
    .filter((token) => token.index <= destination)
    .map((token) => ({ token, value: head.distributionByToken[destination]?.[token.index] ?? 0 }));
}

function peakSource(head: AttentionHead, destination: number) {
  const row = head.distributionByToken[destination] ?? [];
  let best = 0;
  for (let index = 1; index <= destination; index += 1) {
    if ((row[index] ?? 0) > (row[best] ?? 0)) best = index;
  }
  return best;
}

function samplePositions(length: number, count: number) {
  if (length <= count) return Array.from({ length }, (_, index) => index);
  return Array.from({ length: count }, (_, index) => Math.round(index * (length - 1) / (count - 1)));
}

function visibleToken(value: string) {
  return value.trim() || "space";
}
