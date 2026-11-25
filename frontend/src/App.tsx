import { useState } from "react";
import { retestCampaign, retryAnalysisStream, runCrashTestStream } from "./api/client";
import ConfusionClusters from "./components/ConfusionClusters";
import DeltaPanel from "./components/DeltaPanel";
import DisagreementPanel from "./components/DisagreementPanel";
import ErrorBanner from "./components/ErrorBanner";
import FixSuggestions from "./components/FixSuggestions";
import HeadlineMetricsPanel from "./components/HeadlineMetricsPanel";
import PersonaCard from "./components/PersonaCard";
import ScoreBar from "./components/ScoreBar";
import StrengthsPanel from "./components/StrengthsPanel";
import UploadForm from "./components/UploadForm";
import type {
  CampaignInput,
  CrashTestResult,
  FixSuggestion,
  PersonaKind,
  PersonaReaction,
  RetestDelta,
  StreamEvent,
} from "./types";

const initialForm: CampaignInput = {
  ad_format: "text_copy",
  platform: "linkedin_feed",
  advertisement_content: {},
  landing_page: "",
  target_audience: "",
  campaign_objective: "",
};

const DEMO_CAMPAIGN: CampaignInput = {
  ad_format: "text_copy",
  platform: "instagram_feed",
  advertisement_content: {
    text: "Stop letting inflation eat your paycheck. Finley uses institutional-grade AI algorithms to auto-optimize your portfolio 24/7 with zero effort. Join 50,000+ smart investors building generational wealth today. Download now and get a free $50 bonus!",
  },
  landing_page:
    "Welcome to Finley — Wealth on Autopilot.\n\nSign up in 60 seconds and let our proprietary smart engine do the rest. No finance degree required. Terms apply to promotional bonus. Investing involves risk.",
  target_audience: "Young professionals aged 24-35 who want to grow their savings without spending hours researching stocks",
  campaign_objective: "Get app installs and funded accounts",
};

const PERSONA_KIND_GROUPS: { kind: PersonaKind; label: string }[] = [
  { kind: "audience", label: "Audience" },
  { kind: "contrast", label: "Contrast" },
  { kind: "off_target", label: "Off-target" },
];

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
  const [runStageLabel, setRunStageLabel] = useState<string | null>(null);

  function handleStreamEvent(event: StreamEvent) {
    if (event.type === "error") {
      setError(event.message);
      return;
    }
    if (event.type === "stage_error") {
      setStageErrors((prev) => ({ ...prev, [event.stage]: event.message }));
      return;
    }

    if (event.type === "persona") {
      setRunStageLabel("Generating personas...");
    } else if (event.type === "reaction") {
      setRunStageLabel("Reading ads...");
    } else if (
      event.type === "clusters" ||
      event.type === "strengths" ||
      event.type === "headline" ||
      event.type === "scores"
    ) {
      setRunStageLabel("Analyzing reactions...");
    } else if (event.type === "fixes") {
      setRunStageLabel("Generating fixes...");
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
    setRunStageLabel("Generating personas...");
    setRetestDelta(null);
    setResult({ ...EMPTY_RESULT });
    try {
      await runCrashTestStream(input, handleStreamEvent);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setIsRunning(false);
      setRunStageLabel(null);
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

  function handleLoadDemo() {
    setForm(DEMO_CAMPAIGN);
    setError(null);
  }

  function handleDismissError() {
    setError(null);
    setStageErrors({});
  }

  function handleBannerRetry() {
    if (result?.run_id && Object.keys(stageErrors).length > 0) {
      handleRetryAnalysis();
    } else {
      handleSubmit(form);
    }
  }

  const hasAnyResultData = Boolean(
    result &&
      (result.personas.length > 0 ||
        result.reactions.length > 0 ||
        result.summary ||
        result.scores.length > 0 ||
        result.fixes.length > 0 ||
        result.headline_metrics ||
        result.confusion_clusters.length > 0 ||
        result.strengths.length > 0)
  );

  const reactionList = result?.reactions ?? [];
  const stopCount = reactionList.filter((r) => r.would_stop).length;
  const continueCount = reactionList.filter((r) => r.would_continue).length;
  const highTrustCount = reactionList.filter((r) => r.trust_level === "high").length;

  function getReactionKind(reaction: PersonaReaction): PersonaKind | undefined {
    return (
      reaction.kind ||
      result?.personas.find((p) => p.id === reaction.persona_id)?.kind
    );
  }

  const groupedReactions = PERSONA_KIND_GROUPS.map((group) => ({
    ...group,
    items: reactionList.filter((r) => getReactionKind(r) === group.kind),
  })).filter((g) => g.items.length > 0);

  const ungroupedReactions = reactionList.filter((r) => !getReactionKind(r));

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
            runStageLabel={runStageLabel}
          />
        </aside>

        <main className="app-report">
          <div className="report-container">
            <ErrorBanner
              error={error}
              stageErrors={stageErrors}
              onDismiss={handleDismissError}
              onRetry={!isRunning ? handleBannerRetry : undefined}
              isRetrying={isRetryingAnalysis || isRunning}
            />

            {!hasAnyResultData && !isRunning && (
              <div className="empty-state">
                <div className="empty-state__hero">
                  <h1 className="empty-state__title">Test your campaign before you spend</h1>
                  <p className="empty-state__sub">
                    See where your ad loses attention, triggers skepticism, or breaks on the landing page.
                  </p>
                  <button
                    type="button"
                    className="demo-button"
                    onClick={handleLoadDemo}
                  >
                    Load demo campaign
                  </button>
                </div>

                <ol className="steps-strip">
                  <li className="steps-strip__item">
                    <span className="steps-strip__num">1</span>
                    <span className="steps-strip__text">Personas are built from your audience</span>
                  </li>
                  <li className="steps-strip__item">
                    <span className="steps-strip__num">2</span>
                    <span className="steps-strip__text">They each read the ad independently</span>
                  </li>
                  <li className="steps-strip__item">
                    <span className="steps-strip__num">3</span>
                    <span className="steps-strip__text">You see where it breaks and what to fix</span>
                  </li>
                </ol>
              </div>
            )}

            {isRunning && (
              <div className="running-banner">
                <span className="spinner" aria-hidden="true" />
                <span>
                  {runStageLabel || "Running personas against the campaign…"}
                  {result && result.personas.length > 0 && (
                    <span className="running-banner__counts">
                      {" "}({result.personas.length} personas generated, {result.reactions.length} reacted)
                    </span>
                  )}
                </span>
              </div>
            )}

            {result && hasAnyResultData && (
              <div className="report">
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

                {(result.personas.length > 0 || result.reactions.length > 0) && (
                  <section className="report__section">
                    <h2>Persona reactions</h2>

                    <div className="persona-summary-bar" aria-live="polite">
                      <span className="persona-summary-bar__stat">
                        <strong>{result.personas.length}</strong> personas
                      </span>
                      <span className="persona-summary-bar__sep" aria-hidden="true">·</span>
                      <span className="persona-summary-bar__stat">
                        <strong>{reactionList.length}</strong> reacted
                      </span>
                      {reactionList.length > 0 && (
                        <>
                          <span className="persona-summary-bar__sep" aria-hidden="true">·</span>
                          <span className="persona-summary-bar__stat persona-summary-bar__stat--good">
                            <strong>{stopCount}</strong> stop scroll
                          </span>
                          <span className="persona-summary-bar__sep" aria-hidden="true">·</span>
                          <span className="persona-summary-bar__stat persona-summary-bar__stat--good">
                            <strong>{continueCount}</strong> continue
                          </span>
                          <span className="persona-summary-bar__sep" aria-hidden="true">·</span>
                          <span className="persona-summary-bar__stat">
                            <strong>{highTrustCount}</strong> high trust
                          </span>
                        </>
                      )}
                    </div>

                    {groupedReactions.map((group) => (
                      <div key={group.kind} className="persona-group">
                        <h3 className="persona-group__heading">{group.label}</h3>
                        <div className="persona-list">
                          {group.items.map((r) => (
                            <PersonaCard
                              key={r.persona_id}
                              reaction={r}
                              persona={result.personas.find((p) => p.id === r.persona_id)}
                            />
                          ))}
                        </div>
                      </div>
                    ))}

                    {ungroupedReactions.length > 0 && (
                      <div className="persona-group">
                        <div className="persona-list">
                          {ungroupedReactions.map((r) => (
                            <PersonaCard
                              key={r.persona_id}
                              reaction={r}
                              persona={result.personas.find((p) => p.id === r.persona_id)}
                            />
                          ))}
                        </div>
                      </div>
                    )}
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
          </div>
        </main>
      </div>
    </div>
  );
}
