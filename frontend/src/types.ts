export type PersonaKind = "audience" | "contrast" | "off_target";

export type Platform =
  | "instagram_feed"
  | "instagram_story"
  | "facebook_feed"
  | "youtube"
  | "google_search"
  | "email_inbox"
  | "linkedin_feed"
  | "other";

export type AdFormat =
  | "text_copy"
  | "cta_banner"
  | "single_image"
  | "carousel"
  | "video"
  | "search_ad"
  | "email"
  | "audio";

export interface Persona {
  id: string;
  name: string;
  description: string;
  kind: PersonaKind;
  age?: number | null;
  situation?: string | null;
  device?: string | null;
  mood?: string | null;
  prior_experience?: string | null;
  motivation?: string | null;
  skepticism_trigger?: string | null;
  language_region?: string | null;
}

export interface TextCopyContent { text: string; }
export interface CtaBannerContent { headline: string; subtext: string; button_text: string; }
export interface SingleImageContent { image: string; image_media_type: string; ad_platform?: string; }
export interface CarouselContent { images: string[]; image_media_type: string; ad_platform?: string; }
export interface VideoContent { upload_id: string; platform?: string; }
export interface SearchAdContent { headlines: string[]; descriptions: string[]; }
export interface EmailContent { subject: string; preview_text: string; body: string; }
export interface AudioContent { script: string; audio_platform: "podcast_preroll" | "radio" | "other"; }

export interface CampaignInput {
  ad_format: AdFormat;
  platform: Platform;
  advertisement_content: any;
  landing_page?: string;
  landing_page_image?: string;
  landing_page_image_media_type?: string;
  target_audience: string;
  campaign_objective: string;
  persona_ids?: string[] | null;
}

export type StreamEvent =
  | { type: "persona"; data: Persona }
  | { type: "reaction"; data: PersonaReaction }
  | { type: "clusters"; data: { confusion_clusters: ConfusionCluster[]; disagreements: DisagreementPoint[] } }
  | { type: "strengths"; data: { strengths: StrengthPoint[] } }
  | { type: "headline"; data: { headline_metrics: HeadlineMetrics } }
  | { type: "scores"; data: { scores: DimensionScore[] } }
  | { type: "fixes"; data: { fixes: FixSuggestion[] } }
  | { type: "done"; data: { summary: string; run_id?: string } }
  | { type: "stage_error"; stage: string; message: string }
  | { type: "error"; message: string };

export interface PersonaReaction {
  persona_id: string;
  persona_name: string;
  kind?: PersonaKind | null;
  first_read: string;
  reaction: string;
  flags: string[];
  would_stop: boolean;
  would_continue: boolean;
  trust_level: "low" | "medium" | "high";
  would_open?: boolean | null;
  search_competitor_note?: string | null;
}

export interface ConfusionCluster {
  label: string;
  description: string;
  raised_by: string[];
  severity: "low" | "medium" | "high";
}

export interface DisagreementPoint {
  topic: string;
  positions: Record<string, string>;
}

export interface StrengthPoint {
  element: string;
  why_it_works: string;
  personas_who_noticed: string[];
  keep_note: string;
}

export interface HeadlineMetrics {
  total_personas: number;
  stop_count: number;
  continue_count: number;
  stop_rate: number;
  continue_rate: number;
  trust_distribution: Record<string, number>;
  stop_summary: string;
  continue_summary: string;
}

export interface DimensionScore {
  dimension: string;
  score: number;
  reason: string;
}

export interface FixSuggestion {
  target: string;
  issue: string;
  suggestion: string;
  rationale: string;
}

export interface CrashTestResult {
  run_id?: string | null;
  personas: Persona[];
  reactions: PersonaReaction[];
  confusion_clusters: ConfusionCluster[];
  disagreements: DisagreementPoint[];
  strengths: StrengthPoint[];
  headline_metrics?: HeadlineMetrics | null;
  scores: DimensionScore[];
  fixes: FixSuggestion[];
  summary: string;
}

export interface ScoreDelta {
  dimension: string;
  before: number;
  after: number;
  change: number;
  reason_after: string;
}

export interface HeadlineDelta {
  stop_rate_before: number;
  stop_rate_after: number;
  stop_rate_change: number;
  continue_rate_before: number;
  continue_rate_after: number;
  continue_rate_change: number;
  trust_before: Record<string, number>;
  trust_after: Record<string, number>;
}

export interface ClusterChange {
  label: string;
  status: "resolved" | "persisting" | "new";
  matched_with?: string | null;
  reason: string;
}

export interface RetestDelta {
  score_deltas: ScoreDelta[];
  headline_delta: HeadlineDelta;
  cluster_changes: ClusterChange[];
}

export interface RetestResult {
  run_id: string;
  result: CrashTestResult;
  delta: RetestDelta;
}
