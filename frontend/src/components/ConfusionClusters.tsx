import type { ConfusionCluster, PersonaReaction } from "../types";

interface Props {
  clusters: ConfusionCluster[];
  reactions: PersonaReaction[];
}

function nameFor(id: string, reactions: PersonaReaction[]): string {
  return reactions.find((r) => r.persona_id === id)?.persona_name ?? id;
}

export default function ConfusionClusters({ clusters, reactions }: Props) {
  if (clusters.length === 0) return null;

  return (
    <div className="cluster-list">
      {clusters.map((cluster) => (
        <div key={cluster.label} className={`cluster-card cluster-card--${cluster.severity}`}>
          <div className="cluster-card__head">
            <span className="cluster-card__label">{cluster.label}</span>
            <span className="cluster-card__severity">{cluster.severity}</span>
          </div>
          <p className="cluster-card__description">{cluster.description}</p>
          <p className="cluster-card__raised-by">
            Raised by {cluster.raised_by.map((id) => nameFor(id, reactions)).join(", ")}
          </p>
        </div>
      ))}
    </div>
  );
}
