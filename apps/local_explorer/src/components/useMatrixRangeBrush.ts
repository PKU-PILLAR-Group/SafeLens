import {
  useRef,
  useState,
  type MouseEvent as ReactMouseEvent,
  type PointerEvent as ReactPointerEvent
} from "react";

export function useMatrixRangeBrush({
  enabled,
  selectedRange,
  onRangeSelect
}: {
  enabled: boolean;
  selectedRange?: [number, number];
  onRangeSelect: (range?: [number, number]) => void;
}) {
  const dragRef = useRef<{ pointerId: number; start: number; current: number } | null>(null);
  const suppressClickRef = useRef(false);
  const [previewRange, setPreviewRange] = useState<[number, number] | undefined>();
  const activeRange = previewRange ?? selectedRange;

  function tokenAtPoint(event: ReactPointerEvent<HTMLElement>) {
    const root = event.currentTarget;
    const target = document.elementFromPoint(event.clientX, event.clientY)
      ?.closest<HTMLElement>("[data-range-token]");
    if (!target || !root.contains(target)) return undefined;
    const token = Number(target.dataset.rangeToken);
    return Number.isInteger(token) ? token : undefined;
  }

  function onPointerDown(event: ReactPointerEvent<HTMLElement>) {
    if (
      !enabled ||
      event.button !== 0 ||
      event.pointerType === "touch" ||
      event.shiftKey ||
      event.metaKey ||
      event.ctrlKey
    ) return;
    const token = tokenAtPoint(event);
    if (token === undefined) return;
    dragRef.current = { pointerId: event.pointerId, start: token, current: token };
  }

  function onPointerMove(event: ReactPointerEvent<HTMLElement>) {
    const drag = dragRef.current;
    if (!drag || drag.pointerId !== event.pointerId) return;
    const token = tokenAtPoint(event);
    if (token === undefined) return;
    drag.current = token;
    if (drag.current !== drag.start) {
      event.preventDefault();
      if (!event.currentTarget.hasPointerCapture(event.pointerId)) {
        event.currentTarget.setPointerCapture(event.pointerId);
      }
      setPreviewRange(normalizeRange(drag.start, drag.current));
    }
  }

  function finishPointer(event: ReactPointerEvent<HTMLElement>, cancelled: boolean) {
    const drag = dragRef.current;
    if (!drag || drag.pointerId !== event.pointerId) return;
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
    dragRef.current = null;
    setPreviewRange(undefined);
    if (!cancelled && drag.current !== drag.start) {
      suppressClickRef.current = true;
      onRangeSelect(normalizeRange(drag.start, drag.current));
    }
  }

  return {
    activeRange,
    inRange: (token: number) => Boolean(
      activeRange && token >= activeRange[0] && token <= activeRange[1]
    ),
    gridProps: {
      onPointerDown,
      onPointerMove,
      onPointerUp: (event: ReactPointerEvent<HTMLElement>) => finishPointer(event, false),
      onPointerCancel: (event: ReactPointerEvent<HTMLElement>) => finishPointer(event, true),
      onClickCapture: (event: ReactMouseEvent<HTMLElement>) => {
        if (!suppressClickRef.current) return;
        suppressClickRef.current = false;
        event.preventDefault();
        event.stopPropagation();
      }
    }
  };
}

function normalizeRange(left: number, right: number): [number, number] {
  return left <= right ? [left, right] : [right, left];
}

export function tokenRangeToPositions(
  tokens: Array<{ index: number }>,
  range?: [number, number]
): [number, number] | undefined {
  if (!range) return undefined;
  const start = tokens.findIndex((token) => token.index === range[0]);
  const end = tokens.findIndex((token) => token.index === range[1]);
  return start >= 0 && end >= 0 ? normalizeRange(start, end) : undefined;
}

export function positionRangeToTokens(
  tokens: Array<{ index: number }>,
  range?: [number, number]
): [number, number] | undefined {
  if (!range) return undefined;
  const start = tokens[range[0]]?.index;
  const end = tokens[range[1]]?.index;
  return start === undefined || end === undefined ? undefined : normalizeRange(start, end);
}
