import type { RetestDelta } from "../types";

function formatPctDelta(change: number): string {
  const pct = Math.round(change * 100);
  return pct > 0 ? `+${pct}%` : `${pct}%`;
}

function deltaClass(val: number): string {
  if (val > 0) return "delta-val--up";
  if (val < 0) return "delta-val--down";
  return "delta-val--flat";
}

export default function DeltaPanel({ delta }: { delta: RetestDelta }) {
  const { headline_delta: h, score_deltas, cluster_changes } = delta;

  return (
    <div className="delta-panel">
      <div className="delta-headline-row">
        <div className="delta-stat">
          <span className="delta-stat__label">Stop Rate</span>
          <span className="delta-stat__nums">
            {Math.round(h.stop_rate_before * 100)}% → {Math.round(h.stop_rate_after * 100)}%{" "}
            <strong className={deltaClass(h.stop_rate_change)}>
              ({formatPctDelta(h.stop_rate_change)})
            </strong>
          </span>
        </div>
        <div className="delta-stat">
          <span className="delta-stat__label">Continue Rate</span>
          <span className="delta-stat__nums">
            {Math.round(h.continue_rate_before * 100)}% → {Math.round(h.continue_rate_after * 100)}%{" "}
            <strong className={deltaClass(h.continue_rate_change)}>
              ({formatPctDelta(h.continue_rate_change)})
            </strong>
          </span>
        </div>
      </div>

      <div className="delta-scores-grid">
        {score_deltas.map((sd) => (
          <div key={sd.dimension} className="delta-score-chip">
            <span className="delta-score-chip__dim">{sd.dimension}</span>
            <span className="delta-score-chip__val">
              {sd.before} → {sd.after}{" "}
              <strong className={deltaClass(sd.change)}>
                ({sd.change > 0 ? `+${sd.change}` : sd.change})
              </strong>
            </span>
          </div>
        ))}
      </div>

      {cluster_changes.length > 0 && (
        <div className="delta-clusters">
          {cluster_changes.map((cc) => (
            <div key={`${cc.status}-${cc.label}`} className={`delta-cluster delta-cluster--${cc.status}`}>
              <span className={`delta-cluster__badge delta-cluster__badge--${cc.status}`}>
                {cc.status}
              </span>
              <div>
                <strong>{cc.label}</strong>
                {cc.matched_with && cc.matched_with !== cc.label && (
                  <span className="delta-cluster__matched"> (was: {cc.matched_with})</span>
                )}
                <p className="delta-cluster__reason">{cc.reason}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
