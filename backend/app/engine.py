import json
import asyncio
from typing import Any
from pydantic import BaseModel, Field

from app import prompts
from app.config import GROQ_API_KEY, CAMPAIGNCRASH_MODEL, MOCK_MODE
from app.models import (
    CampaignInput,
    ConfusionCluster,
    CrashTestResult,
    DimensionScore,
    DisagreementPoint,
    FixSuggestion,
    Persona,
    PersonaReaction,
)
from app.personas import DEFAULT_PERSONAS

if not MOCK_MODE:
    import groq
    _client = groq.Groq(api_key=GROQ_API_KEY)


class ReactionResult(BaseModel):
    first_read: str = Field(..., description="What this persona thinks the ad/page is offering, in their own words")
    reaction: str = Field(..., description="In-character reaction, written as a quote")
    flags: list[str] = Field(default_factory=list, description="Specific issues this persona noticed")
    would_continue: bool = Field(..., description="Would this persona keep reading / click through?")
    would_open: bool | None = Field(default=None, description="For emails only: would you open this based on subject/preview?")
    search_competitor_note: str | None = Field(default=None, description="For search ads only: how it compares to competitors")

class ClusteringResult(BaseModel):
    clusters: list[ConfusionCluster]
    disagreements: list[DisagreementPoint]

class ScoringResult(BaseModel):
    scores: list[DimensionScore]

class FixesResult(BaseModel):
    fixes: list[FixSuggestion]

def _call_tool(system: str, user: Any, schema: dict, tool_name: str, max_tokens: int = 2000) -> dict:
    if isinstance(user, list):
        groq_user_content = []
        for item in user:
            if item["type"] == "text":
                groq_user_content.append({"type": "text", "text": item["text"]})
            elif item["type"] == "image":
                mime_type = item["source"]["media_type"]
                base64_data = item["source"]["data"]
                groq_user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{base64_data}"}
                })
        user_msg = groq_user_content
    else:
        user_msg = user

    response = _client.chat.completions.create(
        model=CAMPAIGNCRASH_MODEL,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg}
        ],
        tools=[{
            "type": "function",
            "function": {
                "name": tool_name,
                "description": f"Output for {tool_name}",
                "parameters": schema
            }
        }],
        tool_choice={"type": "function", "function": {"name": tool_name}}
    )
    
    tool_calls = response.choices[0].message.tool_calls
    if tool_calls:
        for tool_call in tool_calls:
            if tool_call.function.name == tool_name:
                return json.loads(tool_call.function.arguments)
            
    raise RuntimeError(f"Model failed to return tool use for {tool_name}")


def _selected_personas(persona_ids: list[str] | None) -> list[Persona]:
    if not persona_ids:
        return DEFAULT_PERSONAS
    wanted = set(persona_ids)
    return [p for p in DEFAULT_PERSONAS if p.id in wanted] or DEFAULT_PERSONAS


def _build_user_message(campaign: CampaignInput, text_prompt: str) -> list[dict] | str:
    msg = []
    
    if campaign.ad_format == "single_image":
        content = campaign.advertisement_content
        if content.get("image"):
            msg.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": content.get("image_media_type", "image/png"),
                    "data": content["image"]
                }
            })
    elif campaign.ad_format == "carousel":
        content = campaign.advertisement_content
        for img in content.get("images", []):
            if img:
                msg.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": content.get("image_media_type", "image/png"),
                        "data": img
                    }
                })
    
    if campaign.landing_page_image:
        msg.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": campaign.landing_page_image_media_type,
                "data": campaign.landing_page_image,
            },
        })
        
    if msg:
        msg.append({"type": "text", "text": text_prompt})
        return msg
        
    return text_prompt


def _get_sys_prompt(ad_format: str) -> str:
    format_prompts = {
        "text_copy": prompts.PERSONA_REACTION_SYSTEM,
        "cta_banner": prompts.PERSONA_REACTION_CTA_SYSTEM,
        "single_image": prompts.PERSONA_REACTION_SINGLE_IMAGE_SYSTEM,
        "carousel": prompts.PERSONA_REACTION_CAROUSEL_SYSTEM,
        "video": prompts.PERSONA_REACTION_VIDEO_SYSTEM,
        "search_ad": prompts.PERSONA_REACTION_SEARCH_SYSTEM,
        "email": prompts.PERSONA_REACTION_EMAIL_SYSTEM,
        "audio": prompts.PERSONA_REACTION_AUDIO_SYSTEM,
    }
    return format_prompts.get(ad_format, prompts.PERSONA_REACTION_SYSTEM)


def _format_ad_content_for_prompt(campaign: CampaignInput) -> str:
    # Remove large base64 strings so we don't dump them into text
    content_copy = campaign.advertisement_content.copy()
    if "image" in content_copy:
        content_copy["image"] = "[ATTACHED_IMAGE]"
    if "images" in content_copy:
        content_copy["images"] = ["[ATTACHED_IMAGE]"] * len(content_copy["images"])
    return json.dumps(content_copy, indent=2)


def generate_reactions(campaign: CampaignInput, personas: list[Persona]) -> list[PersonaReaction]:
    if MOCK_MODE:
        return _mock_reactions(campaign, personas)

    reactions: list[PersonaReaction] = []
    sys_prompt = _get_sys_prompt(campaign.ad_format)
    ad_text = _format_ad_content_for_prompt(campaign)

    for persona in personas:
        text_prompt = prompts.PERSONA_REACTION_USER_TEMPLATE.format(
            persona_name=persona.name,
            persona_description=persona.description,
            campaign_objective=campaign.campaign_objective,
            target_audience=campaign.target_audience,
            advertisement=ad_text,
            landing_page=campaign.landing_page or "(See attached image)",
        )
        user = _build_user_message(campaign, text_prompt)
        data = _call_tool(sys_prompt, user, ReactionResult.model_json_schema(), "reaction_result")
        reactions.append(
            PersonaReaction(
                persona_id=persona.id,
                persona_name=persona.name,
                first_read=data["first_read"],
                reaction=data["reaction"],
                flags=data.get("flags", []),
                would_continue=bool(data.get("would_continue", False)),
            )
        )
    return reactions


async def generate_reactions_stream(campaign: CampaignInput, personas: list[Persona]):
    if MOCK_MODE:
        for r in _mock_reactions(campaign, personas):
            yield r
            await asyncio.sleep(0.5)
        return

    sys_prompt = _get_sys_prompt(campaign.ad_format)
    ad_text = _format_ad_content_for_prompt(campaign)

    for persona in personas:
        text_prompt = prompts.PERSONA_REACTION_USER_TEMPLATE.format(
            persona_name=persona.name,
            persona_description=persona.description,
            campaign_objective=campaign.campaign_objective,
            target_audience=campaign.target_audience,
            advertisement=ad_text,
            landing_page=campaign.landing_page or "(See attached image)",
        )
        user = _build_user_message(campaign, text_prompt)
        data = _call_tool(sys_prompt, user, ReactionResult.model_json_schema(), "reaction_result")
        
        reaction_kwargs = {
            "persona_id": persona.id,
            "persona_name": persona.name,
            "first_read": data["first_read"],
            "reaction": data["reaction"],
            "flags": data.get("flags", []),
            "would_continue": bool(data.get("would_continue", False)),
        }
        
        # Need to dynamically add these to model too if applicable? No, model doesn't have them in original.
        # Let's add them to models.py as Optional fields. Oh wait, I didn't add them to models.py yet.
        yield PersonaReaction(**reaction_kwargs)


def cluster_confusion(reactions: list[PersonaReaction]) -> tuple[list[ConfusionCluster], list[DisagreementPoint]]:
    if MOCK_MODE:
        return _mock_clusters(reactions)

    reactions_json = json.dumps([r.model_dump() for r in reactions], indent=2)
    user = prompts.CLUSTER_USER_TEMPLATE.format(reactions_json=reactions_json)
    data = _call_tool(prompts.CLUSTER_SYSTEM, user, ClusteringResult.model_json_schema(), "clustering_result", max_tokens=1500)

    clusters = [ConfusionCluster(**c) for c in data.get("clusters", [])]
    disagreements = [DisagreementPoint(**d) for d in data.get("disagreements", [])]
    return clusters, disagreements


def score_dimensions(reactions: list[PersonaReaction], clusters: list[ConfusionCluster]) -> list[DimensionScore]:
    if MOCK_MODE:
        return _mock_scores(reactions, clusters)

    user = prompts.SCORING_USER_TEMPLATE.format(
        reactions_json=json.dumps([r.model_dump() for r in reactions], indent=2),
        clusters_json=json.dumps([c.model_dump() for c in clusters], indent=2),
    )
    data = _call_tool(prompts.SCORING_SYSTEM, user, ScoringResult.model_json_schema(), "scoring_result", max_tokens=1000)
    return [DimensionScore(**s) for s in data.get("scores", [])]


def suggest_fixes(campaign: CampaignInput, clusters: list[ConfusionCluster]) -> list[FixSuggestion]:
    if MOCK_MODE:
        return _mock_fixes(clusters)

    relevant = [c for c in clusters if c.severity in ("medium", "high")]
    if not relevant:
        return []
        
    ad_text = _format_ad_content_for_prompt(campaign)
    user = prompts.FIX_USER_TEMPLATE.format(
        clusters_json=json.dumps([c.model_dump() for c in relevant], indent=2),
        advertisement=ad_text,
        landing_page=campaign.landing_page or "(See attached image)",
    )
    data = _call_tool(prompts.FIX_SYSTEM, user, FixesResult.model_json_schema(), "fixes_result", max_tokens=1200)
    return [FixSuggestion(**f) for f in data.get("fixes", [])]


def run_crash_test(campaign: CampaignInput) -> CrashTestResult:
    personas = _selected_personas(campaign.persona_ids)
    reactions = generate_reactions(campaign, personas)
    clusters, disagreements = cluster_confusion(reactions)
    scores = score_dimensions(reactions, clusters)
    fixes = suggest_fixes(campaign, clusters)

    high_severity = [c for c in clusters if c.severity in ("medium", "high")]
    summary = (
        f"{len(high_severity)} part{'s' if len(high_severity) != 1 else ''} "
        f"of the campaign may be misunderstood."
        if high_severity
        else "No major misunderstandings surfaced across personas."
    )

    return CrashTestResult(
        reactions=reactions,
        confusion_clusters=clusters,
        disagreements=disagreements,
        scores=scores,
        fixes=fixes,
        summary=summary,
    )

async def run_crash_test_stream(campaign: CampaignInput):
    personas = _selected_personas(campaign.persona_ids)
    reactions = []
    
    async for reaction in generate_reactions_stream(campaign, personas):
        reactions.append(reaction)
        yield {"type": "reaction", "data": reaction.model_dump()}
        
    clusters, disagreements = cluster_confusion(reactions)
    yield {"type": "clusters", "data": {"confusion_clusters": [c.model_dump() for c in clusters], "disagreements": [d.model_dump() for d in disagreements]}}
    
    scores = score_dimensions(reactions, clusters)
    yield {"type": "scores", "data": {"scores": [s.model_dump() for s in scores]}}
    
    fixes = suggest_fixes(campaign, clusters)
    yield {"type": "fixes", "data": {"fixes": [f.model_dump() for f in fixes]}}
    
    high_severity = [c for c in clusters if c.severity in ("medium", "high")]
    summary = (
        f"{len(high_severity)} part{'s' if len(high_severity) != 1 else ''} "
        f"of the campaign may be misunderstood."
        if high_severity
        else "No major misunderstandings surfaced across personas."
    )
    
    yield {"type": "done", "data": {"summary": summary}}


# ---------------------------------------------------------------------------
# Mock mode
# ---------------------------------------------------------------------------

def _mock_reactions(campaign: CampaignInput, personas: list[Persona]) -> list[PersonaReaction]:
    out = []
    
    for i, p in enumerate(personas):
        reaction_text = f"Mock reaction for {campaign.ad_format}."
        flags = ["Mock flag"]
        would_continue = True
        
        # Format-specific distinct behavior
        if campaign.ad_format == "carousel":
            if i % 2 == 0:
                reaction_text = "The first card alone didn't hook me, so I didn't swipe to see the rest."
                would_continue = False
            else:
                reaction_text = "The first card was okay, but seeing the full set made me understand the story better."
        elif campaign.ad_format == "email":
            reaction_text = "I opened it because the subject was compelling, but the body let me down."
            would_continue = False
        elif campaign.ad_format == "search_ad":
            reaction_text = "It stands out against competitors because of the specific numbers."
        elif campaign.ad_format == "audio":
            reaction_text = "I couldn't write down the URL while driving."
            
        out.append(
            PersonaReaction(
                persona_id=p.id,
                persona_name=p.name,
                first_read=f"Mock first read for {campaign.ad_format}",
                reaction=reaction_text,
                flags=flags,
                would_continue=would_continue,
            )
        )
    return out


def _mock_clusters(reactions: list[PersonaReaction]) -> tuple[list[ConfusionCluster], list[DisagreementPoint]]:
    clusters = [
        ConfusionCluster(
            label="Mock Cluster",
            description="Mock description",
            raised_by=["student"],
            severity="high",
        ),
    ]
    disagreements = []
    return clusters, disagreements


def _mock_scores(reactions: list[PersonaReaction], clusters: list[ConfusionCluster]) -> list[DimensionScore]:
    return [
        DimensionScore(dimension="Message Clarity", score=6, reason="Mock reason."),
    ]


def _mock_fixes(clusters: list[ConfusionCluster]) -> list[FixSuggestion]:
    return [
        FixSuggestion(
            target="Headline",
            issue="Mock Cluster",
            suggestion="Mock suggestion",
            rationale="Mock rationale",
        ),
    ]
