import { useState } from "react";
import { runCrashTest, runCrashTestStream } from "./api/client";
import ConfusionClusters from "./components/ConfusionClusters";
import DisagreementPanel from "./components/DisagreementPanel";
import FixSuggestions from "./components/FixSuggestions";
import PersonaCard from "./components/PersonaCard";
import ScoreBar from "./components/ScoreBar";
import UploadForm from "./components/UploadForm";
import type { CampaignInput, CrashTestResult } from "./types";


export default function App() {
  const [result, setResult] = useState<CrashTestResult | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(input: CampaignInput) {
    setIsRunning(true);
    setError(null);
    setResult({ reactions: [], confusion_clusters: [], disagreements: [], scores: [], fixes: [], summary: "" });
    try {
      await runCrashTestStream(input, (event) => {
        setResult((prev) => {
          if (!prev) return prev;
          
          if (event.type === "reaction") {
            return { ...prev, reactions: [...prev.reactions, event.data] };
          } else if (event.type === "clusters") {
            return { ...prev, confusion_clusters: event.data.confusion_clusters, disagreements: event.data.disagreements };
          } else if (event.type === "scores") {
            return { ...prev, scores: event.data.scores };
          } else if (event.type === "fixes") {
            return { ...prev, fixes: event.data.fixes };
          } else if (event.type === "done") {
            return { ...prev, summary: event.data.summary };
          }
          return prev;
        });
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <span className="app-header__mark">CampaignCrash</span>
        <p className="app-header__tagline">
          Crash-test your marketing campaign before you spend money on it.
        </p>
      </header>

      <div className="app-body">
        <aside className="app-sidebar">
          <UploadForm onSubmit={handleSubmit} isRunning={isRunning} />
          {error && <p className="error-banner">{error}</p>}
        </aside>

        <main className="app-report">
          {!result && !isRunning && (
            <div className="empty-state">
              <p>Paste a campaign on the left and run the crash test.</p>
              <p className="empty-state__sub">
                Six personas will read it independently — you'll see where they
                agree, where they don't, and what's likely to be misread.
              </p>
            </div>
          )}

          {isRunning && <div className="empty-state">Running personas against the campaign…</div>}

          {result && (
            <div className="report">
              <p className="report__summary">{result.summary}</p>

              <section className="report__section">
                <h2>Scores</h2>
                <div className="score-list">
                  {result.scores.map((s) => (
                    <ScoreBar key={s.dimension} {...s} />
                  ))}
                </div>
              </section>

              <section className="report__section">
                <h2>Confusion points</h2>
                <ConfusionClusters
                  clusters={result.confusion_clusters}
                  reactions={result.reactions}
                />
              </section>

              {result.disagreements.length > 0 && (
                <section className="report__section">
                  <h2>Where personas disagree</h2>
                  <DisagreementPanel
                    disagreements={result.disagreements}
                    reactions={result.reactions}
                  />
                </section>
              )}

              <section className="report__section">
                <h2>Persona reactions</h2>
                <div className="persona-list">
                  {result.reactions.map((r) => (
                    <PersonaCard key={r.persona_id} reaction={r} />
                  ))}
                </div>
              </section>

              {result.fixes.length > 0 && (
                <section className="report__section">
                  <h2>Suggested fixes</h2>
                  <FixSuggestions fixes={result.fixes} />
                </section>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
