import { useRef } from "react";
import {
  Database,
  Download,
  GitCompareArrows,
  LayoutDashboard,
  PackageOpen,
  Save,
  Search,
  X
} from "lucide-react";

import { useModalDialog } from "../state/useModalDialog";

interface QuickActionsDialogProps {
  open: boolean;
  returnFocusRef: React.RefObject<HTMLElement>;
  context: {
    runId: string;
    sampleId: string;
    view: string;
    layer: number;
    token: number;
    tokenText: string;
  };
  pinnedCount: number;
  onClose: () => void;
  onOverview: () => void;
  onRuns: () => void;
  onTokenSearch: () => void;
  onCompare: () => void;
  onExportSession: () => void;
  onExportArtifact: () => void;
  onExportEvidence: () => void;
}

export function QuickActionsDialog({
  open,
  returnFocusRef,
  context,
  pinnedCount,
  onClose,
  onOverview,
  onRuns,
  onTokenSearch,
  onCompare,
  onExportSession,
  onExportArtifact,
  onExportEvidence
}: QuickActionsDialogProps) {
  const dialogRef = useRef<HTMLElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  const restoreFocusRef = useRef(true);

  useModalDialog({
    open,
    dialogRef,
    initialFocusRef: closeRef,
    returnFocusRef,
    restoreFocusRef,
    onClose
  });

  if (!open) return null;

  return (
    <div
      className="quick-actions-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <aside
        ref={dialogRef}
        className="quick-actions-dialog"
        role="dialog"
        tabIndex={-1}
        aria-modal="true"
        aria-labelledby="quick-actions-title"
      >
        <header>
          <div>
            <span>Global workspace</span>
            <h2 id="quick-actions-title">Quick actions</h2>
          </div>
          <button ref={closeRef} aria-label="Close quick actions" onClick={onClose}>
            <X size={18} />
          </button>
        </header>

        <div className="quick-actions-context" aria-label="Current quick action context">
          <span><b>{context.runId}</b><small>run</small></span>
          <span><b>{context.sampleId}</b><small>sample</small></span>
          <span><b>{context.view}</b><small>view</small></span>
          <span><b>L{context.layer}</b><small>layer</small></span>
          <span><b>{context.tokenText || `T${context.token}`}</b><small>token {context.token}</small></span>
        </div>

        <div className="quick-actions-list" aria-label="Available quick actions">
          <Action icon={<LayoutDashboard size={17} />} label="Open Overview" detail="Evidence map" onClick={execute(onOverview)} />
          <Action icon={<Search size={17} />} label="Find a token" detail="Timeline search" onClick={execute(onTokenSearch)} />
          <Action icon={<Database size={17} />} label="Runs and samples" detail="Run Library" onClick={execute(onRuns)} />
          <Action
            icon={<GitCompareArrows size={17} />}
            label="Compare pinned evidence"
            detail={pinnedCount ? `${pinnedCount} item${pinnedCount === 1 ? "" : "s"} ready` : "Pin evidence first"}
            disabled={!pinnedCount}
            onClick={execute(onCompare)}
          />
          <Action icon={<Save size={17} />} label="Export analysis session" detail="Session JSON" onClick={execute(onExportSession)} />
          <Action icon={<PackageOpen size={17} />} label="Export Explorer artifact" detail="Run JSON" onClick={execute(onExportArtifact)} />
          <Action icon={<Download size={17} />} label="Export current evidence" detail="Evidence JSON" onClick={execute(onExportEvidence)} />
        </div>
      </aside>
    </div>
  );

  function execute(action: () => void) {
    return () => {
      restoreFocusRef.current = false;
      action();
    };
  }
}

function Action({
  icon,
  label,
  detail,
  disabled,
  onClick
}: {
  icon: React.ReactNode;
  label: string;
  detail: string;
  disabled?: boolean;
  onClick: () => void;
}) {
  return (
    <button disabled={disabled} onClick={onClick}>
      <i aria-hidden="true">{icon}</i>
      <span><b>{label}</b><small>{detail}</small></span>
    </button>
  );
}
