import { createContext, useContext, useState, type ReactNode } from "react";

export type MatrixViewportKey =
  | "residual"
  | "attention"
  | "mlp"
  | "attribution"
  | "nla"
  | "patching";
export type MatrixInteractionMode = "select" | "pan";
export type MatrixFitMode = "manual" | "fit";

export interface MatrixViewportSnapshot {
  size: number;
  mode: MatrixInteractionMode;
  axesPinned: boolean;
  fitMode: MatrixFitMode;
}

export type MatrixViewportSnapshots = Partial<Record<MatrixViewportKey, MatrixViewportSnapshot>>;

interface MatrixViewportSessionValue {
  snapshots: MatrixViewportSnapshots;
  onChange: (key: MatrixViewportKey, snapshot: MatrixViewportSnapshot) => void;
}

const MatrixViewportSessionContext = createContext<MatrixViewportSessionValue | null>(null);

export function MatrixViewportSessionProvider({
  snapshots,
  onChange,
  children
}: MatrixViewportSessionValue & { children: ReactNode }) {
  return (
    <MatrixViewportSessionContext.Provider value={{ snapshots, onChange }}>
      {children}
    </MatrixViewportSessionContext.Provider>
  );
}

export function useMatrixViewportSession(
  key: MatrixViewportKey,
  defaults: MatrixViewportSnapshot
) {
  const context = useContext(MatrixViewportSessionContext);
  const [localSnapshot, setLocalSnapshot] = useState(defaults);
  const snapshot = context?.snapshots[key] ?? localSnapshot;
  return {
    snapshot,
    update(next: MatrixViewportSnapshot) {
      if (context) context.onChange(key, next);
      else setLocalSnapshot(next);
    }
  };
}
