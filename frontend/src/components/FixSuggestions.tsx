import { useState } from "react";
import type { AdFormat, FixSuggestion } from "../types";

interface Props {
  fixes: FixSuggestion[];
  adFormat: AdFormat;
  onApplyFix: (fix: FixSuggestion) => "patched" | "copied";
  onRetest?: () => void;
  canRetest?: boolean;
  isRetesting?: boolean;
}

export default function FixSuggestions({
  fixes,
  adFormat,
  onApplyFix,
  onRetest,
  canRetest,
  isRetesting,
}: Props) {
  const [appliedKeys, setAppliedKeys] = useState<Record<string, string>>({});

  if (fixes.length === 0) return null;

  const isAssetFormat = adFormat === "single_image" || adFormat === "carousel" || adFormat === "video";

  function handleApply(fix: FixSuggestion) {
    const key = fix.target + fix.issue;
    const outcome = onApplyFix(fix);
    setAppliedKeys((prev) => ({
      ...prev,
      [key]: outcome === "copied" ? "Copied — upload revised asset on the left" : "Applied to form ✓",
    }));
  }

  return (
    <div className="fix-list">
      {fixes.map((fix) => {
        const key = fix.target + fix.issue;
        const statusMsg = appliedKeys[key];
        return (
          <div key={key} className="fix-card">
            <div className="fix-card__head">
              <span className="fix-card__target">{fix.target}</span>
              <button
                type="button"
                className="fix-card__apply"
                onClick={() => handleApply(fix)}
              >
                {isAssetFormat ? "Copy & Prompt Asset Update" : "Apply"}
              </button>
            </div>
            <p className="fix-card__suggestion">{fix.suggestion}</p>
            <p className="fix-card__rationale">{fix.rationale}</p>
            {statusMsg && <p className="fix-card__status">{statusMsg}</p>}
          </div>
        );
      })}

      {canRetest && onRetest && (
        <div className="retest-bar">
          <button
            type="button"
            className="run-button"
            onClick={onRetest}
            disabled={isRetesting}
          >
            {isRetesting ? "Re-testing with same personas…" : "Re-test revised campaign"}
          </button>
        </div>
      )}
    </div>
  );
}
