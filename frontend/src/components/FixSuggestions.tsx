import type { FixSuggestion } from "../types";

export default function FixSuggestions({ fixes }: { fixes: FixSuggestion[] }) {
  if (fixes.length === 0) return null;

  return (
    <div className="fix-list">
      {fixes.map((fix) => (
        <div key={fix.target + fix.issue} className="fix-card">
          <span className="fix-card__target">{fix.target}</span>
          <p className="fix-card__suggestion">{fix.suggestion}</p>
          <p className="fix-card__rationale">{fix.rationale}</p>
        </div>
      ))}
    </div>
  );
}
