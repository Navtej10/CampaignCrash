import { useState } from "react";
import { retestCampaign, retryAnalysisStream, runCrashTestStream } from "./api/client";
import ConfusionClusters from "./components/ConfusionClusters";
import DeltaPanel from "./components/DeltaPanel";
import DisagreementPanel from "./components/DisagreementPanel";
import FixSuggestions from "./components/FixSuggestions";
import HeadlineMetricsPanel from "./components/HeadlineMetricsPanel";
import PersonaCard from "./components/PersonaCard";
import ScoreBar from "./components/ScoreBar";
import StrengthsPanel from "./components/StrengthsPanel";
import UploadForm from "./components/UploadForm";
import type { CampaignInput, CrashTestResult, FixSuggestion, RetestDelta, StreamEvent } from "./types";

const initialForm: CampaignInput = {
  ad_format: "text_copy",
  platform: "linkedin_feed",
  advertisement_content: {},
  landing_page: "",
  target_audience: "",
  campaign_objective: "",
};

const EMPTY_RESULT: CrashTestResult = {
  run_id: null,
  personas: [],
  reactions: [],
  confusion_clusters: [],
  disagreements: [],
  strengths: [],
  headline_metrics: null,
  scores: [],
  fixes: [],
  summary: "",
};

export default function App() {
  const [form, setForm] = useState<CampaignInput>(initialForm);
  const [result, setResult] = useState<CrashTestResult | null>(null);
  const [retestDelta, setRetestDelta] = useState<RetestDelta | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [isRetryingAnalysis, setIsRetryingAnalysis] = useState(false);
  const [isRetesting, setIsRetesting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stageErrors, setStageErrors] = useState<Record<string, string>>({});

  function handleStreamEvent(event: StreamEvent) {
    if (event.type === "error") {
      setError(event.message);
      return;
    }
    if (event.type === "stage_error") {
      setStageErrors((prev) => ({ ...prev, [event.stage]: event.message }));
      return;
    }
    setResult((prev) => {
      if (!prev) return prev;

      if (event.type === "persona") {
        return { ...prev, personas: [...prev.personas, event.data] };
      } else if (event.type === "reaction") {
        return { ...prev, reactions: [...prev.reactions, event.data] };
      } else if (event.type === "clusters") {
        return {
          ...prev,
          confusion_clusters: event.data.confusion_clusters,
          disagreements: event.data.disagreements,
        };
      } else if (event.type === "strengths") {
        return { ...prev, strengths: event.data.strengths };
      } else if (event.type === "headline") {
        return { ...prev, headline_metrics: event.data.headline_metrics };
      } else if (event.type === "scores") {
        return { ...prev, scores: event.data.scores };
      } else if (event.type === "fixes") {
        return { ...prev, fixes: event.data.fixes };
      } else if (event.type === "done") {
        return { ...prev, summary: event.data.summary, run_id: event.data.run_id ?? prev.run_id };
      }
      return prev;
    });
  }

  async function handleSubmit(input: CampaignInput) {
    setIsRunning(true);
    setError(null);
    setStageErrors({});
    setRetestDelta(null);
    setResult({ ...EMPTY_RESULT });
    try {
      await runCrashTestStream(input, handleStreamEvent);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setIsRunning(false);
    }
  }

  async function handleRetryAnalysis() {
    if (!result?.run_id) return;
    setIsRetryingAnalysis(true);
    setError(null);
    setStageErrors({});
    setResult((prev) =>
      prev
        ? {
            ...prev,
            confusion_clusters: [],
            disagreements: [],
            strengths: [],
            scores: [],
            fixes: [],
            summary: "",
          }
        : prev
    );
    try {
      await retryAnalysisStream(result.run_id, handleStreamEvent);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Retry analysis failed.");
    } finally {
      setIsRetryingAnalysis(false);
    }
  }

  function handleApplyFix(fix: FixSuggestion): "patched" | "copied" {
    if (form.ad_format === "single_image" || form.ad_format === "carousel" || form.ad_format === "video") {
      if (navigator.clipboard) {
        navigator.clipboard.writeText(fix.suggestion).catch(() => {});
      }
      return "copied";
    }

    const targetLower = fix.target.toLowerCase();
    setForm((prev) => {
      if (targetLower.includes("landing")) {
        const existing = prev.landing_page || "";
        return {
          ...prev,
          landing_page: existing ? `${existing}\n\n${fix.suggestion}` : fix.suggestion,
        };
      }

      const content = { ...(prev.advertisement_content || {}) };
      if (prev.ad_format === "text_copy") {
        content.text = content.text ? `${content.text}\n\n${fix.suggestion}` : fix.suggestion;
      } else if (prev.ad_format === "cta_banner") {
        if (targetLower.includes("button") || targetLower.includes("cta")) {
          content.button_text = fix.suggestion;
        } else if (targetLower.includes("subtext")) {
          content.subtext = fix.suggestion;
        } else {
          content.headline = fix.suggestion;
        }
      } else if (prev.ad_format === "email") {
        if (targetLower.includes("subject")) {
          content.subject = fix.suggestion;
        } else if (targetLower.includes("preview")) {
          content.preview_text = fix.suggestion;
        } else {
          content.body = content.body ? `${content.body}\n\n${fix.suggestion}` : fix.suggestion;
        }
      } else if (prev.ad_format === "search_ad") {
        if (targetLower.includes("headline")) {
          const headlines = [...(content.headlines || [""])];
          headlines[0] = fix.suggestion.slice(0, 30);
          content.headlines = headlines;
        } else {
          const descriptions = [...(content.descriptions || [""])];
          descriptions[0] = fix.suggestion.slice(0, 90);
          content.descriptions = descriptions;
        }
      } else if (prev.ad_format === "audio") {
        content.script = content.script ? `${content.script}\n\n${fix.suggestion}` : fix.suggestion;
      }
      return { ...prev, advertisement_content: content };
    });

    return "patched";
  }

  async function handleRetest() {
    if (!result?.run_id) return;
    setIsRetesting(true);
    setError(null);
    try {
      const rt = await retestCampaign(result.run_id, form);
      setResult(rt.result);
      setRetestDelta(rt.delta);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Re-test failed.");
    } finally {
      setIsRetesting(false);
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
          <UploadForm
            form={form}
            onChange={setForm}
            onSubmit={handleSubmit}
            onRetest={handleRetest}
            canRetest={Boolean(result?.run_id)}
            isRunning={isRunning}
            isRetesting={isRetesting}
          />
          {error && <p className="error-banner">{error}</p>}
        </aside>

        <main className="app-report">
          {!result && !isRunning && (
            <div className="empty-state">
              <p>Paste a campaign on the left and run the crash test.</p>
              <p className="empty-state__sub">
                Audience-derived, contrast, and off-target personas will read it
                independently — you'll see where they stop, agree, disagree, and
                what's likely to be misread.
              </p>
            </div>
          )}

          {isRunning && (
            <div className="empty-state">
              Running personas against the campaign…
              {result && result.personas.length > 0 && (
                <span className="empty-state__sub">
                  {" "}({result.personas.length} personas generated, {result.reactions.length} reacted)
                </span>
              )}
            </div>
          )}

          {result && (
            <div className="report">
              {Object.keys(stageErrors).length > 0 && (
                <div className="stage-error-banner">
                  <div className="stage-error-banner__list">
                    {Object.entries(stageErrors).map(([stage, msg]) => (
                      <p key={stage}>
                        <strong>{stage} failed:</strong> {msg}
                      </p>
                    ))}
                  </div>
                  {result.run_id && !isRunning && (
                    <button
                      type="button"
                      className="run-button stage-error-banner__btn"
                      onClick={handleRetryAnalysis}
                      disabled={isRetryingAnalysis}
                    >
                      {isRetryingAnalysis ? "Retrying analysis…" : "Retry analysis"}
                    </button>
                  )}
                </div>
              )}
              {result.summary && <p className="report__summary">{result.summary}</p>}

              {result.headline_metrics && (
                <section className="report__section">
                  <h2>Headline metrics</h2>
                  <HeadlineMetricsPanel metrics={result.headline_metrics} />
                </section>
              )}

              {retestDelta && (
                <section className="report__section">
                  <h2>Before / After Re-test Delta</h2>
                  <DeltaPanel delta={retestDelta} />
                </section>
              )}

              {result.scores.length > 0 && (
                <section className="report__section">
                  <h2>Scores</h2>
                  <div className="score-list">
                    {result.scores.map((s) => (
                      <ScoreBar key={s.dimension} {...s} />
                    ))}
                  </div>
                </section>
              )}

              {result.strengths.length > 0 && (
                <section className="report__section">
                  <h2>What's working, keep this</h2>
                  <StrengthsPanel strengths={result.strengths} reactions={result.reactions} />
                </section>
              )}

              {result.confusion_clusters.length > 0 && (
                <section className="report__section">
                  <h2>Confusion points</h2>
                  <ConfusionClusters
                    clusters={result.confusion_clusters}
                    reactions={result.reactions}
                  />
                </section>
              )}

              {result.disagreements.length > 0 && (
                <section className="report__section">
                  <h2>Where personas disagree</h2>
                  <DisagreementPanel
                    disagreements={result.disagreements}
                    reactions={result.reactions}
                  />
                </section>
              )}

              {result.reactions.length > 0 && (
                <section className="report__section">
                  <h2>Persona reactions</h2>
                  <div className="persona-list">
                    {result.reactions.map((r) => (
                      <PersonaCard
                        key={r.persona_id}
                        reaction={r}
                        persona={result.personas.find((p) => p.id === r.persona_id)}
                      />
                    ))}
                  </div>
                </section>
              )}

              {result.fixes.length > 0 && (
                <section className="report__section">
                  <h2>Suggested fixes</h2>
                  <FixSuggestions
                    fixes={result.fixes}
                    adFormat={form.ad_format}
                    onApplyFix={handleApplyFix}
                    onRetest={handleRetest}
                    canRetest={Boolean(result.run_id)}
                    isRetesting={isRetesting}
                  />
                </section>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
