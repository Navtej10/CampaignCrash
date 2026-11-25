from typing import Optional, Literal
from pydantic import BaseModel, Field, model_validator

PersonaKind = Literal["audience", "contrast", "off_target"]

Platform = Literal[
    "instagram_feed",
    "instagram_story",
    "facebook_feed",
    "youtube",
    "google_search",
    "email_inbox",
    "linkedin_feed",
    "other",
]

AdFormat = Literal[
    "text_copy",
    "cta_banner",
    "single_image",
    "carousel",
    "video",
    "search_ad",
    "email",
    "audio",
]


class Persona(BaseModel):
    id: str
    name: str
    description: str
    kind: PersonaKind = Field(default="contrast", description="audience | contrast | off_target")
    age: int | None = Field(default=None)
    situation: str | None = Field(default=None, description="Where/when they see the ad")
    device: str | None = Field(default=None)
    mood: str | None = Field(default=None)
    prior_experience: str | None = Field(default=None, description="Prior experience with the category")
    motivation: str | None = Field(default=None)
    skepticism_trigger: str | None = Field(default=None)
    language_region: str | None = Field(default=None)


class TextCopyContent(BaseModel):
    text: str


class CtaBannerContent(BaseModel):
    headline: str
    subtext: str
    button_text: str


class SingleImageContent(BaseModel):
    image: str
    image_media_type: str
    ad_platform: str = Field(default="other")


class CarouselContent(BaseModel):
    images: list[str]
    image_media_type: str
    ad_platform: str = Field(default="other")

    @model_validator(mode="after")
    def check_images_length(self) -> "CarouselContent":
        if not (2 <= len(self.images) <= 10):
            raise ValueError("Carousel must have between 2 and 10 images.")
        return self


class VideoContent(BaseModel):
    upload_id: str
    platform: str = Field(default="other")


class SearchAdContent(BaseModel):
    headlines: list[str]
    descriptions: list[str]

    @model_validator(mode="after")
    def check_limits(self) -> "SearchAdContent":
        if len(self.headlines) > 3:
            raise ValueError("Max 3 headlines allowed")
        for h in self.headlines:
            if len(h) > 30:
                raise ValueError("Headline must be 30 chars or less")
        if len(self.descriptions) > 2:
            raise ValueError("Max 2 descriptions allowed")
        for d in self.descriptions:
            if len(d) > 90:
                raise ValueError("Description must be 90 chars or less")
        return self


class EmailContent(BaseModel):
    subject: str
    preview_text: str
    body: str


class AudioContent(BaseModel):
    script: str
    audio_platform: Literal["podcast_preroll", "radio", "other"] = Field(default="other")


class CampaignInput(BaseModel):
    ad_format: AdFormat = Field(..., description="The format of the advertisement")
    platform: Platform = Field(default="other", description="Where the advertisement is seen")
    advertisement_content: dict = Field(..., description="The content of the advertisement")
    landing_page: Optional[str] = Field(default=None, description="Landing page copy the ad sends people to")
    landing_page_image: Optional[str] = Field(default=None, description="Base64-encoded image of the landing page")
    landing_page_image_media_type: Optional[str] = Field(default=None, description="Media type of the image, e.g. 'image/png'")
    target_audience: str = Field(default="", description="Who the company thinks this is for")
    campaign_objective: str = Field(..., description="What the company wants the campaign to do")
    persona_ids: list[str] | None = Field(
        default=None,
        description="Optional subset of persona IDs to run. Omit to run all generated + contrast personas.",
    )

    @model_validator(mode="after")
    def check_landing_page_source(self) -> "CampaignInput":
        has_text = bool(self.landing_page and self.landing_page.strip())
        has_image = bool(self.landing_page_image)
        if has_text and has_image:
            raise ValueError("At most one of landing_page or landing_page_image can be provided.")
        if has_image and not self.landing_page_image_media_type:
            raise ValueError("landing_page_image_media_type is required when landing_page_image is provided.")
        return self

    @model_validator(mode="after")
    def check_advertisement_content(self) -> "CampaignInput":
        format_map = {
            "text_copy": TextCopyContent,
            "cta_banner": CtaBannerContent,
            "single_image": SingleImageContent,
            "carousel": CarouselContent,
            "video": VideoContent,
            "search_ad": SearchAdContent,
            "email": EmailContent,
            "audio": AudioContent,
        }
        model_cls = format_map.get(self.ad_format)
        if not model_cls:
            raise ValueError(f"Unknown ad format: {self.ad_format}")
        try:
            model_cls(**self.advertisement_content)
        except Exception as e:
            raise ValueError(f"Invalid advertisement content for format {self.ad_format}: {e}")
        return self


class PersonaReaction(BaseModel):
    persona_id: str
    persona_name: str
    kind: PersonaKind | None = Field(default=None, description="audience | contrast | off_target")
    first_read: str = Field(..., description="What this persona thinks the ad/page is offering, in their own words")
    reaction: str = Field(..., description="In-character reaction, written as a quote")
    flags: list[str] = Field(default_factory=list, description="Specific issues this persona noticed")
    would_stop: bool = Field(default=False, description="Would this stop the scroll / grab attention?")
    would_continue: bool = Field(..., description="Would this persona keep reading / click through?")
    trust_level: Literal["low", "medium", "high"] = Field(
        default="medium", description="Trust level after reading: low | medium | high"
    )
    would_open: bool | None = Field(default=None, description="For email ads: whether they would open the email")
    search_competitor_note: str | None = Field(default=None, description="For search ads: comparison to competitors")


class ConfusionCluster(BaseModel):
    label: str = Field(..., description="Short name for the issue, e.g. 'Hidden pricing'")
    description: str = Field(..., description="What's actually confusing or misleading")
    raised_by: list[str] = Field(..., description="persona_ids who raised this")
    severity: str = Field(..., description="low | medium | high")


class DisagreementPoint(BaseModel):
    topic: str = Field(..., description="What the personas disagree about")
    positions: dict[str, str] = Field(
        ..., description="persona_id -> that persona's stance on the topic"
    )


class StrengthPoint(BaseModel):
    element: str = Field(..., description="What part of the campaign is working well")
    why_it_works: str = Field(..., description="Why it resonated with personas")
    personas_who_noticed: list[str] = Field(default_factory=list, description="persona_ids who noticed this strength")
    keep_note: str = Field(..., description="Guidance on what to preserve when revising")


class HeadlineMetrics(BaseModel):
    total_personas: int
    stop_count: int
    continue_count: int
    stop_rate: float
    continue_rate: float
    trust_distribution: dict[str, int]
    stop_summary: str
    continue_summary: str


class DimensionScore(BaseModel):
    dimension: str = Field(..., description="e.g. 'Message Clarity'")
    score: int = Field(..., ge=0, le=10)
    reason: str = Field(
        ..., description="Must reference specific persona reactions. Never a bare number."
    )


class FixSuggestion(BaseModel):
    target: str = Field(..., description="What this fix applies to, e.g. 'Headline' or 'CTA'")
    issue: str = Field(..., description="The confusion cluster this addresses")
    suggestion: str = Field(..., description="Concrete rewrite or change")
    rationale: str = Field(..., description="Why this fixes the issue, one line")


class CrashTestResult(BaseModel):
    run_id: str | None = Field(default=None, description="Unique ID for this crash test run")
    personas: list[Persona] = Field(default_factory=list)
    reactions: list[PersonaReaction]
    confusion_clusters: list[ConfusionCluster]
    disagreements: list[DisagreementPoint]
    strengths: list[StrengthPoint] = Field(default_factory=list)
    headline_metrics: HeadlineMetrics | None = Field(default=None)
    scores: list[DimensionScore]
    fixes: list[FixSuggestion]
    summary: str = Field(..., description="One-line closer, e.g. 'Three parts of the campaign may be misunderstood.'")


class ScoreDelta(BaseModel):
    dimension: str
    before: int
    after: int
    change: int
    reason_after: str


class HeadlineDelta(BaseModel):
    stop_rate_before: float
    stop_rate_after: float
    stop_rate_change: float
    continue_rate_before: float
    continue_rate_after: float
    continue_rate_change: float
    trust_before: dict[str, int]
    trust_after: dict[str, int]


class ClusterChange(BaseModel):
    label: str
    status: Literal["resolved", "persisting", "new"]
    matched_with: str | None = None
    reason: str


class RetestDelta(BaseModel):
    score_deltas: list[ScoreDelta]
    headline_delta: HeadlineDelta
    cluster_changes: list[ClusterChange]


class RetestRequest(BaseModel):
    run_id: str
    revised_input: CampaignInput


class RetestResult(BaseModel):
    run_id: str
    result: CrashTestResult
    delta: RetestDelta
