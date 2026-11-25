import type { PersonaReaction, StrengthPoint } from "../types";

interface Props {
  strengths: StrengthPoint[];
  reactions: PersonaReaction[];
}

function nameFor(id: string, reactions: PersonaReaction[]): string {
  return reactions.find((r) => r.persona_id === id)?.persona_name ?? id;
}

export default function StrengthsPanel({ strengths, reactions }: Props) {
  if (strengths.length === 0) return null;

  return (
    <div className="strength-list">
      {strengths.map((s) => (
        <div key={s.element} className="strength-card">
          <div className="strength-card__head">
            <span className="strength-card__element">{s.element}</span>
            <span className="strength-card__badge">Keep this</span>
          </div>
          <p className="strength-card__why">{s.why_it_works}</p>
          <p className="strength-card__keep">
            <strong>Preserve:</strong> {s.keep_note}
          </p>
          {s.personas_who_noticed.length > 0 && (
            <p className="strength-card__personas">
              Noticed by {s.personas_who_noticed.map((id) => nameFor(id, reactions)).join(", ")}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}
