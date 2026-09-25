export interface Persona {
  id: string;
  name: string;
  description: string;
}

export type AdFormat = "text_copy" | "cta_banner" | "single_image" | "carousel" | "video" | "search_ad" | "email" | "audio";

export interface TextCopyContent { text: string; }
export interface CtaBannerContent { headline: string; subtext: string; button_text: string; }
export interface SingleImageContent { image: string; image_media_type: string; ad_platform: string; }
export interface CarouselContent { images: string[]; image_media_type: string; ad_platform: string; }
export interface VideoContent { upload_id: string; platform: string; }
export interface SearchAdContent { headlines: string[]; descriptions: string[]; }
export interface EmailContent { subject: string; preview_text: string; body: string; }
export interface AudioContent { script: string; audio_platform: "podcast_preroll" | "radio" | "other"; }

export interface CampaignInput {
  ad_format: AdFormat;
  advertisement_content: any; // Handled dynamically in form
  landing_page?: string;
  landing_page_image?: string;
  landing_page_image_media_type?: string;
  target_audience: string;
  campaign_objective: string;
  persona_ids?: string[] | null;
}

export type StreamEvent = 
  | { type: "reaction"; data: PersonaReaction }
  | { type: "clusters"; data: { confusion_clusters: ConfusionCluster[]; disagreements: DisagreementPoint[] } }
  | { type: "scores"; data: { scores: DimensionScore[] } }
  | { type: "fixes"; data: { fixes: FixSuggestion[] } }
  | { type: "done"; data: { summary: string } };

export interface PersonaReaction {
  persona_id: string;
  persona_name: string;
  first_read: string;
  reaction: string;
  flags: string[];
  would_continue: boolean;
  would_open?: boolean; // For email
  search_competitor_note?: string; // For search
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
  reactions: PersonaReaction[];
  confusion_clusters: ConfusionCluster[];
  disagreements: DisagreementPoint[];
  scores: DimensionScore[];
  fixes: FixSuggestion[];
  summary: string;
}
