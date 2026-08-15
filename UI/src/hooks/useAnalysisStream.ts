import { useEffect, useState } from "react";
import { sessionStreamUrl } from "../lib/apiClient";

export interface StreamStatus {
  sessionStatus: string;
  nodeStatus: string | null;
}

/** Subscribes to a session's SSE progress stream. Closes the connection
 * once the session reaches a terminal status; the underlying background
 * run is unaffected by the browser disconnecting (plan.md Section 4). */
export function useAnalysisStream(sessionId: string | undefined): StreamStatus | null {
  const [status, setStatus] = useState<StreamStatus | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    setStatus(null);

    const source = new EventSource(sessionStreamUrl(sessionId));

    const handleStatus = (event: MessageEvent) => {
      const data = JSON.parse(event.data) as { session_status: string; node_status: string | null };
      const next: StreamStatus = { sessionStatus: data.session_status, nodeStatus: data.node_status ?? null };
      setStatus(next);
      if (next.sessionStatus === "completed" || next.sessionStatus === "failed") {
        source.close();
      }
    };

    source.addEventListener("status", handleStatus as EventListener);
    source.addEventListener("error", () => source.close());

    return () => source.close();
  }, [sessionId]);

  return status;
}
