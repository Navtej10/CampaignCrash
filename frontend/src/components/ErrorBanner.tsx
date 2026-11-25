import { useState } from "react";

interface Props {
  error: string | null;
  stageErrors: Record<string, string>;
  onDismiss: () => void;
  onRetry?: () => void;
  isRetrying?: boolean;
}

function mapFriendlyError(rawMessages: string[], hasStageErrors: boolean): string {
  const combined = rawMessages.join(" ").toLowerCase();

  if (
    combined.includes("rate limit") ||
    combined.includes("429") ||
    combined.includes("too many requests") ||
    combined.includes("quota")
  ) {
    return "We hit a rate limit with the AI provider. Wait a moment and try again.";
  }

  if (
    combined.includes("failed to fetch") ||
    combined.includes("network") ||
    combined.includes("econnrefused") ||
    combined.includes("timeout") ||
    combined.includes("timed out") ||
    combined.includes("no response body")
  ) {
    return "Network error — couldn't reach the analysis server. Check your connection and retry.";
  }

  if (
    hasStageErrors ||
    combined.includes("analysis") ||
    combined.includes("parse") ||
    combined.includes("json") ||
    combined.includes("status 500") ||
    combined.includes("internal server error")
  ) {
    return "Part of the analysis failed to complete. Any personas and reactions already generated are preserved below.";
  }

  return "Something went wrong while running the crash test. You can retry or check the details below.";
}

export default function ErrorBanner({
  error,
  stageErrors,
  onDismiss,
  onRetry,
  isRetrying,
}: Props) {
  const [showDetails, setShowDetails] = useState(false);

  const stageEntries = Object.entries(stageErrors);
  if (!error && stageEntries.length === 0) {
    return null;
  }

  const rawMessages = [
    ...(error ? [error] : []),
    ...stageEntries.map(([stage, msg]) => `${stage}: ${msg}`),
  ];

  const friendlyMessage = mapFriendlyError(rawMessages, stageEntries.length > 0);

  return (
    <div className="results-error-banner" role="alert">
      <div className="results-error-banner__top">
        <div className="results-error-banner__content">
          <p className="results-error-banner__message">{friendlyMessage}</p>
        </div>
        <button
          type="button"
          className="results-error-banner__dismiss"
          onClick={onDismiss}
          aria-label="Dismiss error"
          title="Dismiss"
        >
          ×
        </button>
      </div>

      <div className="results-error-banner__actions">
        {onRetry && (
          <button
            type="button"
            className="results-error-banner__retry"
            onClick={onRetry}
            disabled={isRetrying}
          >
            {isRetrying ? "Retrying…" : "Retry"}
          </button>
        )}
        <button
          type="button"
          className="results-error-banner__details-btn"
          onClick={() => setShowDetails((prev) => !prev)}
          aria-expanded={showDetails}
        >
          {showDetails ? "Hide details" : "Show details"}
        </button>
      </div>

      {showDetails && (
        <pre className="results-error-banner__details">
          {rawMessages.join("\n")}
        </pre>
      )}
    </div>
  );
}
