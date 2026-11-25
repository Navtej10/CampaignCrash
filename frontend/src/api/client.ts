import type { CampaignInput, CrashTestResult, RetestResult, StreamEvent } from "../types";

export async function runCrashTest(input: CampaignInput): Promise<CrashTestResult> {
  const res = await fetch("/api/crash-test", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed with status ${res.status}`);
  }

  return res.json();
}

export async function retestCampaign(
  runId: string,
  revisedInput: CampaignInput
): Promise<RetestResult> {
  const res = await fetch("/api/crash-test/retest", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ run_id: runId, revised_input: revisedInput }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Retest failed with status ${res.status}`);
  }

  return res.json();
}

async function _readSseStream(
  res: Response,
  onEvent: (event: StreamEvent) => void
): Promise<void> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed with status ${res.status}`);
  }

  if (!res.body) throw new Error("No response body");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");

    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const dataStr = line.slice(6);
        try {
          const event = JSON.parse(dataStr) as StreamEvent;
          onEvent(event);
        } catch (err) {
          console.error("Failed to parse SSE line", dataStr, err);
        }
      }
    }
  }
}

export async function runCrashTestStream(
  input: CampaignInput,
  onEvent: (event: StreamEvent) => void
): Promise<void> {
  const res = await fetch("/api/crash-test/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  return _readSseStream(res, onEvent);
}

export async function retryAnalysisStream(
  runId: string,
  onEvent: (event: StreamEvent) => void
): Promise<void> {
  const res = await fetch(`/api/crash-test/${encodeURIComponent(runId)}/retry-analysis`, {
    method: "POST",
  });
  return _readSseStream(res, onEvent);
}
