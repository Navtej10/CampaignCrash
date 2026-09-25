import type { PersonaReaction } from "../types";

export default function PersonaCard({ reaction }: { reaction: PersonaReaction }) {
  return (
    <div className="persona-card">
      <div className="persona-card__head">
        <span className="persona-card__name">{reaction.persona_name}</span>
        <span
          className={`persona-card__continue persona-card__continue--${
            reaction.would_continue ? "yes" : "no"
          }`}
        >
          {reaction.would_continue ? "Would continue" : "Would bounce"}
        </span>
      </div>

      {reaction.would_open !== undefined && reaction.would_open !== null && (
        <p className="persona-card__first-read" style={{ marginBottom: "8px" }}>
          <span>Would Open Email:</span> {reaction.would_open ? "Yes" : "No"}
        </p>
      )}

      {reaction.search_competitor_note && (
        <p className="persona-card__first-read" style={{ marginBottom: "8px" }}>
          <span>Competitor Comparison:</span> {reaction.search_competitor_note}
        </p>
      )}

      <p className="persona-card__first-read">
        <span>Understood offer as:</span> {reaction.first_read}
      </p>

      <blockquote className="persona-card__quote">{reaction.reaction}</blockquote>

      {reaction.flags.length > 0 && (
        <ul className="persona-card__flags">
          {reaction.flags.map((flag) => (
            <li key={flag}>{flag}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
