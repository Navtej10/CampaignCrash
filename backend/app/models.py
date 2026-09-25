from typing import Optional, Literal
from pydantic import BaseModel, Field, model_validator

class Persona(BaseModel):
    id: str
    name: str
    description: str
    platform_notes: dict[str, str] | None = Field(default=None)

AdFormat = Literal["text_copy", "cta_banner", "single_image", "carousel", "video", "search_ad", "email", "audio"]

class TextCopyContent(BaseModel):
    text: str

class CtaBannerContent(BaseModel):
    headline: str
    subtext: str
    button_text: str

class SingleImageContent(BaseModel):
    image: str
    image_media_type: str
    ad_platform: Literal["instagram_feed", "instagram_story", "facebook_feed", "youtube_thumbnail", "other"]

class CarouselContent(BaseModel):
    images: list[str]
    image_media_type: str
    ad_platform: str
    
    @model_validator(mode="after")
    def check_images_length(self) -> "CarouselContent":
        if not (2 <= len(self.images) <= 10):
            raise ValueError("Carousel must have between 2 and 10 images.")
        return self

class VideoContent(BaseModel):
    upload_id: str
    platform: Literal["reels", "tiktok_style", "youtube_instream", "other"]

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
    audio_platform: Literal["podcast_preroll", "radio", "other"]


class CampaignInput(BaseModel):
    ad_format: AdFormat = Field(..., description="The format of the advertisement")
    advertisement_content: dict = Field(..., description="The content of the advertisement")
    landing_page: Optional[str] = Field(default=None, description="Landing page copy the ad sends people to")
    landing_page_image: Optional[str] = Field(default=None, description="Base64-encoded image of the landing page")
    landing_page_image_media_type: Optional[str] = Field(default=None, description="Media type of the image, e.g. 'image/png'")
    target_audience: str = Field(..., description="Who the company thinks this is for")
    campaign_objective: str = Field(..., description="What the company wants the campaign to do")
    persona_ids: list[str] | None = Field(
        default=None,
        description="Subset of DEFAULT_PERSONAS to run. Omit to run all of them.",
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
    first_read: str = Field(..., description="What this persona thinks the ad/page is offering, in their own words")
    reaction: str = Field(..., description="In-character reaction, written as a quote")
    flags: list[str] = Field(default_factory=list, description="Specific issues this persona noticed")
    would_continue: bool = Field(..., description="Would this persona keep reading / click through?")
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
    reactions: list[PersonaReaction]
    confusion_clusters: list[ConfusionCluster]
    disagreements: list[DisagreementPoint]
    scores: list[DimensionScore]
    fixes: list[FixSuggestion]
    summary: str = Field(..., description="One-line closer, e.g. 'Three parts of the campaign may be misunderstood.'")
