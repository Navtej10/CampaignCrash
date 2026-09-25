import type { CampaignInput, CrashTestResult, StreamEvent } from "../types";

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

export async function runCrashTestStream(
  input: CampaignInput,
  onEvent: (event: StreamEvent) => void
): Promise<void> {
  const res = await fetch("/api/crash-test/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });

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
    
    // The last element is either empty (if buffer ends with \n\n) or an incomplete event
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
