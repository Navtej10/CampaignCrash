import type { DimensionScore } from "../types";

export default function ScoreBar({ dimension, score, reason }: DimensionScore) {
  const pct = Math.round((score / 10) * 100);
  const level = score >= 7 ? "good" : score >= 4 ? "mid" : "low";

  return (
    <div className={`score-bar score-bar--${level}`}>
      <div className="score-bar__head">
        <span className="score-bar__dimension">{dimension}</span>
        <span className="score-bar__value">{score}/10</span>
      </div>
      <div className="score-bar__track">
        <div className="score-bar__fill" style={{ width: `${pct}%` }} />
      </div>
      <p className="score-bar__reason">{reason}</p>
    </div>
  );
}
