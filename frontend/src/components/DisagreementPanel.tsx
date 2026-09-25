import type { DisagreementPoint, PersonaReaction } from "../types";

interface Props {
  disagreements: DisagreementPoint[];
  reactions: PersonaReaction[];
}

function nameFor(id: string, reactions: PersonaReaction[]): string {
  return reactions.find((r) => r.persona_id === id)?.persona_name ?? id;
}

export default function DisagreementPanel({ disagreements, reactions }: Props) {
  if (disagreements.length === 0) return null;

  return (
    <div className="disagreement-panel">
      {disagreements.map((d) => (
        <div key={d.topic} className="disagreement-card">
          <p className="disagreement-card__topic">{d.topic}</p>
          <div className="disagreement-card__positions">
            {Object.entries(d.positions).map(([personaId, stance]) => (
              <div key={personaId} className="disagreement-card__position">
                <span className="disagreement-card__persona">{nameFor(personaId, reactions)}</span>
                <span>{stance}</span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
