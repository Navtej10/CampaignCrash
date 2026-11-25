import type { HeadlineMetrics } from "../types";

export default function HeadlineMetricsPanel({ metrics }: { metrics: HeadlineMetrics }) {
  const stopPct = Math.round(metrics.stop_rate * 100);
  const contPct = Math.round(metrics.continue_rate * 100);
  const { high = 0, medium = 0, low = 0 } = metrics.trust_distribution;

  return (
    <div className="headline-metrics">
      <div className="headline-metric-card">
        <span className="headline-metric-card__label">Scroll Stop Rate</span>
        <span className="headline-metric-card__value">{metrics.stop_summary}</span>
        <span className="headline-metric-card__sub">{stopPct}% stopped</span>
      </div>
      <div className="headline-metric-card">
        <span className="headline-metric-card__label">Continue / Click Rate</span>
        <span className="headline-metric-card__value">{metrics.continue_summary}</span>
        <span className="headline-metric-card__sub">{contPct}% would continue</span>
      </div>
      <div className="headline-metric-card">
        <span className="headline-metric-card__label">Trust Distribution</span>
        <div className="trust-pills">
          <span className="trust-pill trust-pill--high">High: {high}</span>
          <span className="trust-pill trust-pill--medium">Med: {medium}</span>
          <span className="trust-pill trust-pill--low">Low: {low}</span>
        </div>
      </div>
    </div>
  );
}
