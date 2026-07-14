import { ExplorerApiError } from "./api/explorerClient";

export type JobFailureKind =
  | "network"
  | "request"
  | "compatibility"
  | "authorization"
  | "protocol"
  | "computation";

export type JobFailurePhase = "submission" | "stream" | "execution" | "cancellation";

export interface JobFailure {
  kind: JobFailureKind;
  phase: JobFailurePhase;
  title: string;
  message: string;
  code: string;
  serverCode?: string;
  httpStatus?: number;
  occurredAt: string;
}

export function jobFailureFromError(
  error: unknown,
  phase: JobFailurePhase,
  fallbackMessage: string
): JobFailure {
  if (error instanceof ExplorerApiError) {
    const kind = classifyApiError(error);
    return createJobFailure({
      kind,
      phase,
      message: error.message,
      code: error.code,
      serverCode: error.serverCode,
      httpStatus: error.httpStatus
    });
  }
  if (error instanceof TypeError) {
    return createJobFailure({
      kind: "network",
      phase,
      message: error.message || fallbackMessage,
      code: `${phase}_transport_error`
    });
  }
  return createJobFailure({
    kind: phase === "execution" ? "computation" : "request",
    phase,
    message: error instanceof Error ? error.message : fallbackMessage,
    code: `${phase}_error`
  });
}

export function jobProtocolFailure(message: string, code: string): JobFailure {
  return createJobFailure({ kind: "protocol", phase: "stream", message, code });
}

export function jobStreamFailure(message: string): JobFailure {
  return createJobFailure({
    kind: "network",
    phase: "stream",
    message,
    code: "progress_stream_disconnected"
  });
}

export function jobComputationFailure(jobKind: string, message: string): JobFailure {
  return createJobFailure({
    kind: "computation",
    phase: "execution",
    message,
    code: `${jobKind}_execution_error`
  });
}

export function jobFailureKindLabel(kind: JobFailureKind) {
  switch (kind) {
    case "network": return "Network";
    case "request": return "Request";
    case "compatibility": return "Compatibility";
    case "authorization": return "Authorization";
    case "protocol": return "Protocol";
    case "computation": return "Computation";
  }
}

export function jobFailureRecovery(failure: JobFailure) {
  switch (failure.kind) {
    case "network":
      return "Check the local API connection, then retry. The source Run is unchanged.";
    case "request":
      return "Review the current inputs and retry. No result was added to the Run Library.";
    case "compatibility":
      return "Choose a compatible model, layer, component, or token context before retrying.";
    case "authorization":
      return "Confirm the required local model access or credentials, then run preflight again.";
    case "protocol":
      return "Retry once. If the response remains invalid, copy diagnostics and check API compatibility.";
    case "computation":
      return "The worker stopped without replacing the source Run. Copy diagnostics before retrying.";
  }
}

function classifyApiError(error: ExplorerApiError): JobFailureKind {
  const serverCode = error.serverCode?.toLowerCase() ?? "";
  if (
    error.httpStatus === 401 || error.httpStatus === 403 ||
    /(authorization|gated|credential|token_required|access_required)/.test(serverCode)
  ) return "authorization";
  if (
    error.httpStatus === 409 ||
    /(incompatible|preflight|model_not_allowed|layer_unavailable|component_unsupported)/.test(serverCode)
  ) return "compatibility";
  if (error.code.startsWith("invalid_")) return "protocol";
  return "request";
}

function createJobFailure(input: Omit<JobFailure, "title" | "occurredAt">): JobFailure {
  return {
    ...input,
    title: failureTitle(input.kind, input.phase),
    occurredAt: new Date().toISOString()
  };
}

function failureTitle(kind: JobFailureKind, phase: JobFailurePhase) {
  if (phase === "cancellation") return "Cancellation request failed";
  switch (kind) {
    case "network": return "Workspace connection interrupted";
    case "request": return "Job request rejected";
    case "compatibility": return "Job inputs are incompatible";
    case "authorization": return "Job authorization required";
    case "protocol": return "Job response is invalid";
    case "computation": return "Job computation failed";
  }
}
