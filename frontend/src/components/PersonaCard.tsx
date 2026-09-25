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
          {reaction.flags.map((flag) => {
            const lowerFlag = flag.toLowerCase();
            const isPlatformNote = lowerFlag.includes("platform note") || lowerFlag.includes("scroll") || lowerFlag.includes("illegible");
            const isVideoHook = lowerFlag.includes("3-second hook assessment") || lowerFlag.includes("hook assessment");
            const isVideoMuted = lowerFlag.includes("muted viewing assessment") || lowerFlag.includes("muted");
            
            const cleanFlag = flag.replace(/^Platform Note:\s*/i, "");
            
            return (
              <li key={flag}>
                {isPlatformNote && (
                  <span style={{ backgroundColor: "#e2e8f0", color: "#475569", padding: "2px 6px", borderRadius: "4px", fontSize: "0.85em", marginRight: "6px", fontWeight: 500 }}>📱 Platform</span>
                )}
                {isVideoHook && (
                  <span style={{ backgroundColor: "#fef08a", color: "#854d0e", padding: "2px 6px", borderRadius: "4px", fontSize: "0.85em", marginRight: "6px", fontWeight: 500 }}>⏱️ First 3 Seconds</span>
                )}
                {isVideoMuted && (
                  <span style={{ backgroundColor: "#d9f99d", color: "#3f6212", padding: "2px 6px", borderRadius: "4px", fontSize: "0.85em", marginRight: "6px", fontWeight: 500 }}>🔇 Muted Viewing</span>
                )}
                {cleanFlag}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
