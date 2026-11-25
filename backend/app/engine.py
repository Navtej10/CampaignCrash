import asyncio
import json
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from pydantic import BaseModel, Field

from app import prompts
from app.config import GROQ_API_KEY, CAMPAIGNCRASH_MODEL, MOCK_MODE
from app.models import (
    CampaignInput,
    ClusterChange,
    ConfusionCluster,
    CrashTestResult,
    DimensionScore,
    DisagreementPoint,
    FixSuggestion,
    HeadlineDelta,
    HeadlineMetrics,
    Persona,
    PersonaReaction,
    RetestDelta,
    RetestResult,
    ScoreDelta,
    StrengthPoint,
)
from app.personas import (
    FIXED_CONTRAST_PERSONAS,
    PLATFORM_CONTEXT,
    build_language_lens_persona,
)

if not MOCK_MODE:
    import groq

    _client = groq.Groq(api_key=GROQ_API_KEY)


# ---------------------------------------------------------------------------
# In-memory run store with TTL for apples-to-apples re-testing
# ---------------------------------------------------------------------------

RUN_STORE_TTL_SECONDS = 3600
_RUN_STORE: dict[str, dict[str, Any]] = {}


def _prune_run_store() -> None:
    now = time.time()
    expired = [k for k, v in _RUN_STORE.items() if now - v["created_at"] > RUN_STORE_TTL_SECONDS]
    for k in expired:
        _RUN_STORE.pop(k, None)


def save_run(
    run_id: str,
    personas: list[Persona],
    campaign: CampaignInput,
    result: CrashTestResult | None = None,
    reactions: list[PersonaReaction] | None = None,
) -> None:
    _prune_run_store()
    _RUN_STORE[run_id] = {
        "personas": personas,
        "campaign": campaign,
        "result": result,
        "reactions": reactions if reactions is not None else (result.reactions if result else []),
        "created_at": time.time(),
    }


def get_run(run_id: str) -> dict[str, Any] | None:
    _prune_run_store()
    return _RUN_STORE.get(run_id)


# ---------------------------------------------------------------------------
# Tool schemas for structured LLM outputs
# ---------------------------------------------------------------------------

class GeneratedAudienceBatchResult(BaseModel):
    audience_personas: list[Persona] = Field(..., description="Exactly 2 distinct audience-derived personas")


class GeneratedOffTargetResult(BaseModel):
    off_target_persona: Persona = Field(..., description="Exactly 1 off-target persona")


class ReactionResult(BaseModel):
    first_read: str = Field(..., description="What this persona thinks the ad/page is offering, in their own words")
    reaction: str = Field(..., description="In-character reaction, written as a quote")
    flags: list[str] = Field(default_factory=list, description="Specific issues this persona noticed")
    would_stop: bool = Field(..., description="Would this stop the scroll / grab attention?")
    would_continue: bool = Field(..., description="Would this persona keep reading / click through?")
    trust_level: str = Field(..., description="low | medium | high")
    would_open: bool | None = Field(default=None, description="For emails only: would you open this based on subject/preview?")
    search_competitor_note: str | None = Field(default=None, description="For search ads only: how it compares to competitors")


class ClusteringResult(BaseModel):
    clusters: list[ConfusionCluster]
    disagreements: list[DisagreementPoint]


class StrengthsResult(BaseModel):
    strengths: list[StrengthPoint]


class ScoringResult(BaseModel):
    scores: list[DimensionScore]


class FixesResult(BaseModel):
    fixes: list[FixSuggestion]


class ClusterMatchResult(BaseModel):
    changes: list[ClusterChange]


def _create_with_retry(kwargs: dict, max_attempts: int = 4):
    for attempt in range(max_attempts):
        try:
            return _client.chat.completions.create(**kwargs)
        except groq.RateLimitError as e:
            if attempt == max_attempts - 1:
                raise
            response = getattr(e, "response", None)
            retry_after = response.headers.get("retry-after") if response else None
            time.sleep(float(retry_after) if retry_after else 5 * 2**attempt)
        except groq.BadRequestError as e:
            if "tool_use_failed" not in str(e) or attempt == max_attempts - 1:
                raise
            time.sleep(1.0)


def _to_groq_user_content(user: Any) -> Any:
    if not isinstance(user, list):
        return user
    groq_user_content = []
    for item in user:
        if item["type"] == "text":
            groq_user_content.append({"type": "text", "text": item["text"]})
        elif item["type"] == "image":
            mime_type = item["source"]["media_type"]
            base64_data = item["source"]["data"]
            groq_user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{base64_data}"},
            })
    return groq_user_content


def _call_json_fallback(sys_prompt: str, user: Any, schema: dict, max_tokens: int) -> dict:
    system = (
        sys_prompt
        + "\n\nReturn ONLY one JSON object matching this schema. No prose, no markdown fences:\n"
        + json.dumps(schema)
    )
    kwargs: dict[str, Any] = {
        "model": CAMPAIGNCRASH_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": _to_groq_user_content(user)},
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": min(max_tokens, 700),
        "temperature": 0.2,
    }
    if "qwen3" in CAMPAIGNCRASH_MODEL.lower():
        kwargs["reasoning_effort"] = "none"

    resp = _create_with_retry(kwargs)
    choice = resp.choices[0]
    if choice.finish_reason == "length":
        raise RuntimeError("Model output was cut off. Reduce output size or raise max_tokens.")
    return json.loads(choice.message.content)


def _call_tool(
    system: str,
    user: Any,
    schema: dict,
    tool_name: str,
    max_tokens: int = 700,
    temperature: float | None = 0.3,
) -> dict:
    user_msg = _to_groq_user_content(user)

    kwargs: dict[str, Any] = {
        "model": CAMPAIGNCRASH_MODEL,
        "max_tokens": min(max_tokens, 700),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
        "tools": [{
            "type": "function",
            "function": {
                "name": tool_name,
                "description": f"Output for {tool_name}",
                "parameters": schema,
            },
        }],
        "tool_choice": {"type": "function", "function": {"name": tool_name}},
    }
    if temperature is not None:
        kwargs["temperature"] = temperature
    if "qwen3" in CAMPAIGNCRASH_MODEL.lower():
        kwargs["reasoning_effort"] = "none"

    try:
        response = _create_with_retry(kwargs)
    except groq.BadRequestError as e:
        if "tool_use_failed" in str(e):
            return _call_json_fallback(system, user, schema, kwargs.get("max_tokens", 700))
        raise

    tool_calls = response.choices[0].message.tool_calls
    if tool_calls:
        for tool_call in tool_calls:
            if tool_call.function.name == tool_name:
                return json.loads(tool_call.function.arguments)

    raise RuntimeError(f"Model failed to return tool use for {tool_name}")


# ---------------------------------------------------------------------------
# Stage 1: Persona generation
# ---------------------------------------------------------------------------

def generate_personas(campaign: CampaignInput) -> list[Persona]:
    """Generate 4 audience-derived personas + 1 off_target + fixed contrast personas."""
    audience_text = (campaign.target_audience or "").strip()
    if not audience_text:
        audience_text = "General digital consumers evaluating an online product or service"

    if MOCK_MODE:
        roster = _mock_generate_personas(audience_text, campaign)
    else:
        audience_personas: list[Persona] = []
        for batch_idx in range(2):
            existing_names = ", ".join(p.name for p in audience_personas) or "none yet"
            user = prompts.PERSONA_GEN_AUDIENCE_BATCH_TEMPLATE.format(
                target_audience=audience_text,
                campaign_objective=campaign.campaign_objective,
                platform=campaign.platform,
                ad_format=campaign.ad_format,
                existing_names=existing_names,
            )
            data = _call_tool(
                prompts.PERSONA_GEN_SYSTEM,
                user,
                GeneratedAudienceBatchResult.model_json_schema(),
                "generated_audience_batch_result",
                max_tokens=700,
            )
            for idx, p in enumerate(data.get("audience_personas", [])[:2]):
                p_copy = dict(p)
                p_copy["kind"] = "audience"
                p_copy.setdefault("id", f"audience_{batch_idx * 2 + idx + 1}")
                audience_personas.append(Persona(**p_copy))

        off_target_user = prompts.PERSONA_GEN_OFF_TARGET_TEMPLATE.format(
            target_audience=audience_text,
            campaign_objective=campaign.campaign_objective,
            platform=campaign.platform,
            ad_format=campaign.ad_format,
        )
        off_target_data = _call_tool(
            prompts.PERSONA_GEN_SYSTEM,
            off_target_user,
            GeneratedOffTargetResult.model_json_schema(),
            "generated_off_target_result",
            max_tokens=700,
        )
        off_target_raw = dict(off_target_data.get("off_target_persona", {}))
        off_target_raw["kind"] = "off_target"
        off_target_raw.setdefault("id", "off_target")
        off_target_persona = Persona(**off_target_raw)

        contrast = list(FIXED_CONTRAST_PERSONAS) + [build_language_lens_persona(audience_text)]
        roster = audience_personas + contrast + [off_target_persona]

    if campaign.persona_ids:
        wanted = set(campaign.persona_ids)
        filtered = [p for p in roster if p.id in wanted]
        if filtered:
            return filtered
    return roster


# ---------------------------------------------------------------------------
# Stage 2: Persona reactions
# ---------------------------------------------------------------------------

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
                    "data": content["image"],
                },
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
                        "data": img,
                    },
                })
    elif campaign.ad_format == "video":
        upload_id = campaign.advertisement_content.get("upload_id")
        import glob
        import os
        import base64
        from app.video import extract_frames, transcribe_audio, get_video_metadata

        temp_dir = os.path.join(os.getcwd(), "temp_videos")
        video_files = glob.glob(os.path.join(temp_dir, f"{upload_id}_*")) if upload_id else []
        if video_files:
            video_path = video_files[0]
            frames = extract_frames(video_path, interval_seconds=1.0)
            transcript = transcribe_audio(video_path)
            meta = get_video_metadata(video_path)

            for i, frame in enumerate(frames):
                msg.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": base64.b64encode(frame).decode("utf-8"),
                    },
                })
                msg.append({"type": "text", "text": f"Frame at ~{i}s"})

            text_prompt += f"\n\nVideo Metadata: {meta}\nTranscript: {transcript}\nPlatform Context: {campaign.platform}"

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
    content_copy = campaign.advertisement_content.copy()
    if "image" in content_copy:
        content_copy["image"] = "[ATTACHED_IMAGE]"
    if "images" in content_copy:
        content_copy["images"] = ["[ATTACHED_IMAGE]"] * len(content_copy["images"])
    return json.dumps(content_copy, indent=2)


def _build_reaction_prompt(campaign: CampaignInput, persona: Persona, ad_text: str) -> str:
    has_lp = bool(campaign.landing_page or campaign.landing_page_image)
    if has_lp:
        lp_section = "--- LANDING PAGE ---\n" + (campaign.landing_page or "(See attached image)")
        flags_inst = "a short list of specific things that confused you, felt hidden, or didn't match between the ad and the landing page"
    else:
        lp_section = "No landing page was provided — react to the ad on its own; don't assume or invent what happens after a click."
        flags_inst = "a short list of specific things that confused you, felt hidden, or didn't make sense in the ad"

    platform_ctx = PLATFORM_CONTEXT.get(campaign.platform, PLATFORM_CONTEXT["other"])
    return prompts.PERSONA_REACTION_USER_TEMPLATE.format(
        persona_name=persona.name,
        persona_kind=persona.kind,
        persona_description=persona.description,
        age=persona.age or "Adult",
        situation=persona.situation or "Browsing online",
        device=persona.device or "Mobile phone",
        mood=persona.mood or "Skimming",
        prior_experience=persona.prior_experience or "Familiar with similar ads",
        motivation=persona.motivation or "Decide quickly if this is relevant",
        skepticism_trigger=persona.skepticism_trigger or "Vague claims or hidden pricing",
        language_region=persona.language_region or "English (General)",
        platform=campaign.platform,
        platform_context=platform_ctx,
        campaign_objective=campaign.campaign_objective,
        target_audience=campaign.target_audience or "General audience",
        advertisement=ad_text,
        landing_page_section=lp_section,
        flags_instruction=flags_inst,
    )


def _react_single_persona(campaign: CampaignInput, persona: Persona, sys_prompt: str, ad_text: str) -> PersonaReaction:
    text_prompt = _build_reaction_prompt(campaign, persona, ad_text)
    user = _build_user_message(campaign, text_prompt)
    data = _call_tool(sys_prompt, user, ReactionResult.model_json_schema(), "reaction_result")
    trust = str(data.get("trust_level", "medium")).lower()
    if trust not in ("low", "medium", "high"):
        trust = "medium"
    return PersonaReaction(
        persona_id=persona.id,
        persona_name=persona.name,
        kind=persona.kind,
        first_read=data["first_read"],
        reaction=data["reaction"],
        flags=data.get("flags", []),
        would_stop=bool(data.get("would_stop", False)),
        would_continue=bool(data.get("would_continue", False)),
        trust_level=trust,  # type: ignore[arg-type]
        would_open=data.get("would_open"),
        search_competitor_note=data.get("search_competitor_note"),
    )


def generate_reactions(campaign: CampaignInput, personas: list[Persona]) -> list[PersonaReaction]:
    if MOCK_MODE:
        return _mock_reactions(campaign, personas)

    sys_prompt = _get_sys_prompt(campaign.ad_format)
    ad_text = _format_ad_content_for_prompt(campaign)
    return [_react_single_persona(campaign, p, sys_prompt, ad_text) for p in personas]


async def generate_reactions_stream(campaign: CampaignInput, personas: list[Persona]):
    if MOCK_MODE:
        for r in _mock_reactions(campaign, personas):
            yield r
            await asyncio.sleep(0.25)
        return

    sys_prompt = _get_sys_prompt(campaign.ad_format)
    ad_text = _format_ad_content_for_prompt(campaign)
    for p in personas:
        yield await asyncio.to_thread(_react_single_persona, campaign, p, sys_prompt, ad_text)


# ---------------------------------------------------------------------------
# Stage 3a & 3b: Clustering & Strengths (parallel)
# ---------------------------------------------------------------------------

def cluster_confusion(reactions: list[PersonaReaction]) -> tuple[list[ConfusionCluster], list[DisagreementPoint]]:
    if MOCK_MODE:
        return _mock_clusters(reactions)

    reactions_json = json.dumps([r.model_dump() for r in reactions], indent=2)
    user = prompts.CLUSTER_USER_TEMPLATE.format(reactions_json=reactions_json)
    data = _call_tool(prompts.CLUSTER_SYSTEM, user, ClusteringResult.model_json_schema(), "clustering_result", max_tokens=700)

    clusters = [ConfusionCluster(**c) for c in data.get("clusters", [])]
    disagreements = [DisagreementPoint(**d) for d in data.get("disagreements", [])]
    return clusters, disagreements


def identify_strengths(reactions: list[PersonaReaction]) -> list[StrengthPoint]:
    if MOCK_MODE:
        return _mock_strengths(reactions)

    reactions_json = json.dumps([r.model_dump() for r in reactions], indent=2)
    user = prompts.STRENGTHS_USER_TEMPLATE.format(reactions_json=reactions_json)
    data = _call_tool(prompts.STRENGTHS_SYSTEM, user, StrengthsResult.model_json_schema(), "strengths_result", max_tokens=700)
    return [StrengthPoint(**s) for s in data.get("strengths", [])]


# ---------------------------------------------------------------------------
# Stage 4: Deterministic Headline Metrics + Anchored Scoring (low temp)
# ---------------------------------------------------------------------------

def compute_headline_metrics(reactions: list[PersonaReaction]) -> HeadlineMetrics:
    total = len(reactions)
    stop_count = sum(1 for r in reactions if r.would_stop)
    continue_count = sum(1 for r in reactions if r.would_continue)
    trust_dist = {"low": 0, "medium": 0, "high": 0}
    for r in reactions:
        if r.trust_level in trust_dist:
            trust_dist[r.trust_level] += 1

    stop_rate = round(stop_count / total, 2) if total else 0.0
    continue_rate = round(continue_count / total, 2) if total else 0.0
    return HeadlineMetrics(
        total_personas=total,
        stop_count=stop_count,
        continue_count=continue_count,
        stop_rate=stop_rate,
        continue_rate=continue_rate,
        trust_distribution=trust_dist,
        stop_summary=f"{stop_count} of {total} would stop",
        continue_summary=f"{continue_count} of {total} would continue",
    )


def score_dimensions(
    reactions: list[PersonaReaction],
    clusters: list[ConfusionCluster],
    campaign_objective: str = "",
) -> list[DimensionScore]:
    if MOCK_MODE:
        return _mock_scores(reactions, clusters, campaign_objective)

    user = prompts.SCORING_USER_TEMPLATE.format(
        campaign_objective=campaign_objective or "Not specified",
        reactions_json=json.dumps([r.model_dump() for r in reactions], indent=2),
        clusters_json=json.dumps([c.model_dump() for c in clusters], indent=2),
    )
    data = _call_tool(
        prompts.SCORING_SYSTEM,
        user,
        ScoringResult.model_json_schema(),
        "scoring_result",
        max_tokens=700,
        temperature=0.1,
    )
    return [DimensionScore(**s) for s in data.get("scores", [])]


# ---------------------------------------------------------------------------
# Stage 5: Fix Suggestions
# ---------------------------------------------------------------------------

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
        landing_page=campaign.landing_page or "(No landing page)",
    )
    data = _call_tool(prompts.FIX_SYSTEM, user, FixesResult.model_json_schema(), "fixes_result", max_tokens=700)
    return [FixSuggestion(**f) for f in data.get("fixes", [])]


# ---------------------------------------------------------------------------
# Pipeline Orchestrators
# ---------------------------------------------------------------------------

def _build_summary(clusters: list[ConfusionCluster]) -> str:
    high_severity = [c for c in clusters if c.severity in ("medium", "high")]
    return (
        f"{len(high_severity)} part{'s' if len(high_severity) != 1 else ''} "
        f"of the campaign may be misunderstood."
        if high_severity
        else "No major misunderstandings surfaced across personas."
    )


def _run_evaluation_with_personas(campaign: CampaignInput, personas: list[Persona], run_id: str) -> CrashTestResult:
    reactions = generate_reactions(campaign, personas)
    with ThreadPoolExecutor(max_workers=2) as pool:
        f_clusters = pool.submit(cluster_confusion, reactions)
        f_strengths = pool.submit(identify_strengths, reactions)
        clusters, disagreements = f_clusters.result()
        strengths = f_strengths.result()

    headline_metrics = compute_headline_metrics(reactions)
    scores = score_dimensions(reactions, clusters, campaign.campaign_objective)
    fixes = suggest_fixes(campaign, clusters)
    summary = _build_summary(clusters)

    return CrashTestResult(
        run_id=run_id,
        personas=personas,
        reactions=reactions,
        confusion_clusters=clusters,
        disagreements=disagreements,
        strengths=strengths,
        headline_metrics=headline_metrics,
        scores=scores,
        fixes=fixes,
        summary=summary,
    )


def run_crash_test(campaign: CampaignInput) -> CrashTestResult:
    run_id = str(uuid.uuid4())
    personas = generate_personas(campaign)
    result = _run_evaluation_with_personas(campaign, personas, run_id)
    save_run(run_id, personas, campaign, result)
    return result


def _format_stage_error(exc: Exception) -> str:
    if not MOCK_MODE and isinstance(exc, groq.RateLimitError):
        return "Rate limit hit. Wait a minute and retry, or switch model."
    return str(exc)


async def _stream_analysis_stages(
    run_id: str,
    campaign: CampaignInput,
    personas: list[Persona],
    reactions: list[PersonaReaction],
):
    clusters: list[ConfusionCluster] = []
    disagreements: list[DisagreementPoint] = []
    strengths: list[StrengthPoint] = []
    scores: list[DimensionScore] = []
    fixes: list[FixSuggestion] = []

    cluster_res, strengths_res = await asyncio.gather(
        asyncio.to_thread(cluster_confusion, reactions),
        asyncio.to_thread(identify_strengths, reactions),
        return_exceptions=True,
    )

    if isinstance(cluster_res, Exception):
        yield {
            "type": "stage_error",
            "stage": "clustering",
            "message": _format_stage_error(cluster_res),
        }
    else:
        clusters, disagreements = cluster_res
        yield {
            "type": "clusters",
            "data": {
                "confusion_clusters": [c.model_dump() for c in clusters],
                "disagreements": [d.model_dump() for d in disagreements],
            },
        }

    if isinstance(strengths_res, Exception):
        yield {
            "type": "stage_error",
            "stage": "strengths",
            "message": _format_stage_error(strengths_res),
        }
    else:
        strengths = strengths_res
        yield {"type": "strengths", "data": {"strengths": [s.model_dump() for s in strengths]}}

    headline_metrics = compute_headline_metrics(reactions)
    yield {"type": "headline", "data": {"headline_metrics": headline_metrics.model_dump()}}

    try:
        scores = await asyncio.to_thread(score_dimensions, reactions, clusters, campaign.campaign_objective)
        yield {"type": "scores", "data": {"scores": [s.model_dump() for s in scores]}}
    except Exception as exc:
        yield {
            "type": "stage_error",
            "stage": "scoring",
            "message": _format_stage_error(exc),
        }

    try:
        fixes = await asyncio.to_thread(suggest_fixes, campaign, clusters)
        yield {"type": "fixes", "data": {"fixes": [f.model_dump() for f in fixes]}}
    except Exception as exc:
        yield {
            "type": "stage_error",
            "stage": "fixes",
            "message": _format_stage_error(exc),
        }

    summary = _build_summary(clusters)
    result = CrashTestResult(
        run_id=run_id,
        personas=personas,
        reactions=reactions,
        confusion_clusters=clusters,
        disagreements=disagreements,
        strengths=strengths,
        headline_metrics=headline_metrics,
        scores=scores,
        fixes=fixes,
        summary=summary,
    )
    save_run(run_id, personas, campaign, result, reactions=reactions)
    yield {"type": "done", "data": {"summary": summary, "run_id": run_id}}


async def run_crash_test_stream(campaign: CampaignInput):
    run_id = str(uuid.uuid4())
    personas = await asyncio.to_thread(generate_personas, campaign)
    for p in personas:
        yield {"type": "persona", "data": p.model_dump()}
        if MOCK_MODE:
            await asyncio.sleep(0.08)

    reactions: list[PersonaReaction] = []
    async for reaction in generate_reactions_stream(campaign, personas):
        reactions.append(reaction)
        yield {"type": "reaction", "data": reaction.model_dump()}

    # Persist reactions immediately so analysis can be retried if any later stage fails.
    save_run(run_id, personas, campaign, result=None, reactions=reactions)

    async for event in _stream_analysis_stages(run_id, campaign, personas, reactions):
        yield event


async def retry_analysis_stream(run_id: str):
    entry = get_run(run_id)
    if not entry:
        raise KeyError(f"Run {run_id} not found or expired")

    personas: list[Persona] = entry["personas"]
    campaign: CampaignInput = entry["campaign"]
    reactions: list[PersonaReaction] = entry.get("reactions") or (
        entry["result"].reactions if entry.get("result") else []
    )

    async for event in _stream_analysis_stages(run_id, campaign, personas, reactions):
        yield event


# ---------------------------------------------------------------------------
# Phase 3: Re-test & Delta computation
# ---------------------------------------------------------------------------

def match_clusters(
    before_clusters: list[ConfusionCluster],
    after_clusters: list[ConfusionCluster],
) -> list[ClusterChange]:
    if MOCK_MODE:
        return _mock_match_clusters(before_clusters, after_clusters)

    user = prompts.CLUSTER_MATCH_USER_TEMPLATE.format(
        before_clusters_json=json.dumps([c.model_dump() for c in before_clusters], indent=2),
        after_clusters_json=json.dumps([c.model_dump() for c in after_clusters], indent=2),
    )
    data = _call_tool(
        prompts.CLUSTER_MATCH_SYSTEM,
        user,
        ClusterMatchResult.model_json_schema(),
        "cluster_match_result",
        max_tokens=700,
        temperature=0.1,
    )
    return [ClusterChange(**c) for c in data.get("changes", [])]


def retest_campaign(run_id: str, revised_input: CampaignInput) -> RetestResult:
    entry = get_run(run_id)
    if not entry:
        raise KeyError(f"Run {run_id} not found or expired")

    personas: list[Persona] = entry["personas"]
    before_result: CrashTestResult = entry["result"]

    after_result = _run_evaluation_with_personas(revised_input, personas, run_id)

    before_scores_map = {s.dimension: s.score for s in before_result.scores}
    score_deltas = [
        ScoreDelta(
            dimension=s.dimension,
            before=before_scores_map.get(s.dimension, s.score),
            after=s.score,
            change=s.score - before_scores_map.get(s.dimension, s.score),
            reason_after=s.reason,
        )
        for s in after_result.scores
    ]

    bh = before_result.headline_metrics or compute_headline_metrics(before_result.reactions)
    ah = after_result.headline_metrics or compute_headline_metrics(after_result.reactions)
    headline_delta = HeadlineDelta(
        stop_rate_before=bh.stop_rate,
        stop_rate_after=ah.stop_rate,
        stop_rate_change=round(ah.stop_rate - bh.stop_rate, 2),
        continue_rate_before=bh.continue_rate,
        continue_rate_after=ah.continue_rate,
        continue_rate_change=round(ah.continue_rate - bh.continue_rate, 2),
        trust_before=bh.trust_distribution,
        trust_after=ah.trust_distribution,
    )

    cluster_changes = match_clusters(before_result.confusion_clusters, after_result.confusion_clusters)
    delta = RetestDelta(
        score_deltas=score_deltas,
        headline_delta=headline_delta,
        cluster_changes=cluster_changes,
    )

    save_run(run_id, personas, revised_input, after_result)
    return RetestResult(run_id=run_id, result=after_result, delta=delta)


# ---------------------------------------------------------------------------
# Mock mode
# ---------------------------------------------------------------------------

def _mock_generate_personas(audience_text: str, campaign: CampaignInput) -> list[Persona]:
    audience_personas = [
        Persona(
            id="audience_maya",
            name="Maya Chen",
            kind="audience",
            description=f"Target buyer ({audience_text}) evaluating practical fit and time savings.",
            age=32,
            situation=f"Scrolling {campaign.platform.replace('_', ' ')} during a 5-minute coffee break",
            device="iPhone 15",
            mood="Curious, time-pressed",
            prior_experience="Tried 2 similar tools last year",
            motivation=f"Achieve: {campaign.campaign_objective or 'solve workflow friction'}",
            skepticism_trigger="Vague promises without concrete proof or setup time",
            language_region="English (US)",
        ),
        Persona(
            id="audience_david",
            name="David Okafor",
            kind="audience",
            description=f"Decision-maker in ({audience_text}) looking for clear ROI before clicking.",
            age=41,
            situation=f"Checking {campaign.platform.replace('_', ' ')} between meetings",
            device="MacBook Pro",
            mood="Analytical, focused",
            prior_experience="Currently paying for an older category tool",
            motivation="Reduce wasted spend and get clear outcomes",
            skepticism_trigger="Missing pricing or unclear target fit",
            language_region="English (UK/Global)",
        ),
        Persona(
            id="audience_sofia",
            name="Sofia Alvarez",
            kind="audience",
            description=f"Hands-on practitioner in ({audience_text}) who wants immediate clarity.",
            age=26,
            situation="Browsing on the train home after work",
            device="Android phone",
            mood="Tired, impatient with fluff",
            prior_experience="Follows category creators but rarely clicks ads",
            motivation="Spot something genuinely useful in under 3 seconds",
            skepticism_trigger="Generic buzzwords and stock-sounding claims",
            language_region="English / Spanish bilingual (US)",
        ),
        Persona(
            id="audience_liam",
            name="Liam Patel",
            kind="audience",
            description=f"Early adopter in ({audience_text}) comparing modern alternatives.",
            age=29,
            situation="Late-night browsing while researching solutions",
            device="iPad / Mobile",
            mood="Exploratory, detail-oriented",
            prior_experience="Reads reviews and landing pages closely",
            motivation="Verify whether the offer actually matches the headline",
            skepticism_trigger="Headline-to-landing-page mismatch",
            language_region="English (Canada)",
        ),
    ]
    off_target = Persona(
        id="off_target",
        name="Harold Jenkins (Off-target)",
        kind="off_target",
        description=(
            f"Retiree outside '{audience_text}' who stumbled on the ad in his feed and "
            "reads the copy literally with zero category context."
        ),
        age=68,
        situation="Scrolling feed in the evening while watching TV",
        device="iPad",
        mood="Relaxed, easily confused by tech/insider phrasing",
        prior_experience="None in this category",
        motivation="Only clicks if it clearly explains what it is in plain English",
        skepticism_trigger="Insider jargon or unclear who this is even for",
        language_region="English (US)",
    )
    contrast = list(FIXED_CONTRAST_PERSONAS) + [build_language_lens_persona(audience_text)]
    return audience_personas + contrast + [off_target]


def _mock_reactions(campaign: CampaignInput, personas: list[Persona]) -> list[PersonaReaction]:
    out = []
    has_lp = bool(campaign.landing_page or campaign.landing_page_image)
    ad_str = json.dumps(campaign.advertisement_content).lower()
    has_price = "$" in ad_str or "free" in ad_str or "price" in ad_str
    has_proof = any(ch.isdigit() for ch in ad_str)

    for i, p in enumerate(personas):
        flags = []
        would_stop = i % 2 == 0 or p.kind == "audience"
        would_continue = p.kind == "audience" and (i % 3 != 2)
        trust_level: str = "high" if (p.kind == "audience" and has_proof) else "medium"

        if p.id == "price_sensitive" and not has_price:
            reaction_text = f"On {campaign.platform}, I looked for the price immediately and didn't see one—makes me assume it's expensive."
            flags = ["Missing upfront pricing triggers fee skepticism"]
            would_continue = False
            trust_level = "low"
        elif p.id == "claim_skeptic" and not has_proof:
            reaction_text = "Lots of broad promises without concrete numbers or methodology—why should I believe this works?"
            flags = ["Unverified claim lacks specific proof or numbers"]
            would_continue = False
            trust_level = "low"
        elif p.id == "competitor_loyalist":
            reaction_text = "I already use a tool for this; the ad doesn't explain why switching is worth the hassle."
            flags = ["Unclear differentiation vs existing alternatives"]
            would_continue = False
            trust_level = "medium"
        elif p.kind == "off_target":
            reaction_text = "I'm not sure who this is for—the phrasing feels aimed at insiders and doesn't explain the basics."
            flags = ["Off-target audience misreads core offer"]
            would_stop = False
            would_continue = False
            trust_level = "low"
        elif campaign.ad_format == "email":
            reaction_text = "The subject caught my eye in my inbox, though the body needs a clearer next step."
            flags = ["CTA in email body could be sharper"]
        elif campaign.ad_format == "video":
            reaction_text = "Watched muted in feed—first 3 seconds hook okay, captions carry the message."
            flags = ["Passed muted viewing assessment"]
        else:
            reaction_text = f"In {campaign.platform.replace('_', ' ')}, the main hook lands, though { 'the landing page needs tighter alignment' if has_lp else 'I want clearer proof before clicking'}."
            flags = ["Landing page mismatch" if has_lp else "Wants clearer next-step detail"]

        out.append(
            PersonaReaction(
                persona_id=p.id,
                persona_name=p.name,
                kind=p.kind,
                first_read=f"Interprets {campaign.ad_format} on {campaign.platform} as an offer for {campaign.campaign_objective or 'this product'}.",
                reaction=reaction_text,
                flags=flags,
                would_stop=would_stop,
                would_continue=would_continue,
                trust_level=trust_level,  # type: ignore[arg-type]
                would_open=(i % 2 == 0) if campaign.ad_format == "email" else None,
                search_competitor_note="Needs stronger numeric differentiation vs top 3 search results." if campaign.ad_format == "search_ad" else None,
            )
        )
    return out


def _mock_clusters(reactions: list[PersonaReaction]) -> tuple[list[ConfusionCluster], list[DisagreementPoint]]:
    raised_price = [r.persona_id for r in reactions if "pricing" in " ".join(r.flags).lower()] or [reactions[0].persona_id]
    raised_proof = [r.persona_id for r in reactions if "proof" in " ".join(r.flags).lower() or "claim" in " ".join(r.flags).lower()] or [reactions[-1].persona_id]
    clusters = [
        ConfusionCluster(
            label="Hidden or unclear pricing",
            description="Price-sensitive and analytical readers cannot tell what this costs upfront.",
            raised_by=raised_price,
            severity="high",
        ),
        ConfusionCluster(
            label="Unbacked claims",
            description="Key benefits lack concrete numbers, proof, or differentiation from alternatives.",
            raised_by=raised_proof,
            severity="medium",
        ),
    ]
    disagreements = []
    if len(reactions) >= 2:
        disagreements.append(
            DisagreementPoint(
                topic="Hook clarity vs. skepticism",
                positions={
                    reactions[0].persona_id: "Found the opening hook relevant enough to pause.",
                    reactions[-1].persona_id: "Did not understand who the offer is actually for.",
                },
            )
        )
    return clusters, disagreements


def _mock_strengths(reactions: list[PersonaReaction]) -> list[StrengthPoint]:
    noticed = [r.persona_id for r in reactions if r.would_stop][:3]
    return [
        StrengthPoint(
            element="Opening hook framing",
            why_it_works="Target audience personas immediately recognized the problem space in-feed.",
            personas_who_noticed=noticed,
            keep_note="Keep the core problem framing when tightening pricing and proof.",
        )
    ]


def _mock_scores(
    reactions: list[PersonaReaction],
    clusters: list[ConfusionCluster],
    campaign_objective: str = "",
) -> list[DimensionScore]:
    has_high = any(c.severity == "high" for c in clusters)
    obj_label = campaign_objective or "stated objective"
    return [
        DimensionScore(dimension="Message Clarity", score=7, reason="Target personas grasped the core offer, though off-target readers missed context."),
        DimensionScore(dimension="Value Proposition", score=6, reason="Benefit is clear to Maya Chen, but Competitor loyalist sees weak differentiation."),
        DimensionScore(dimension="Potential Confusion", score=4 if has_high else 7, reason="High-severity pricing ambiguity flagged by Price-sensitive buyer."),
        DimensionScore(dimension="Accessibility", score=7, reason="First-time customer followed the main point; Language lens wants simpler phrasing."),
        DimensionScore(dimension="Claim Evidence", score=4, reason="Claim skeptic flagged missing numbers or verifiable proof."),
        DimensionScore(dimension="Attention", score=6, reason="Stops target personas in-feed, though off-target and skeptical readers scroll past."),
        DimensionScore(dimension="Objective Fit", score=6, reason=f"Supports '{obj_label}' directionally, but missing CTA/proof weakens conversion."),
        DimensionScore(dimension="Trust", score=5, reason="Mixed trust: audience personas are open, while Price-sensitive and Claim skeptic report low trust."),
    ]


def _mock_fixes(clusters: list[ConfusionCluster]) -> list[FixSuggestion]:
    fixes = []
    for c in clusters:
        if c.severity in ("medium", "high"):
            if "pric" in c.label.lower():
                fixes.append(
                    FixSuggestion(
                        target="Body / Pricing line",
                        issue=c.label,
                        suggestion="Add transparent pricing (e.g., '$19/mo, cancel anytime — 14-day free trial, no card required').",
                        rationale="Removes fee suspicion for Price-sensitive buyer and First-time customer.",
                    )
                )
            else:
                fixes.append(
                    FixSuggestion(
                        target="Headline",
                        issue=c.label,
                        suggestion="Replace broad adjectives with one concrete metric (e.g., 'Cut onboarding time by 42% in 7 days').",
                        rationale="Gives Claim skeptic and Competitor loyalist a verifiable reason to switch.",
                    )
                )
    return fixes


def _mock_match_clusters(
    before_clusters: list[ConfusionCluster],
    after_clusters: list[ConfusionCluster],
) -> list[ClusterChange]:
    before_labels = {c.label for c in before_clusters}
    after_labels = {c.label for c in after_clusters}
    changes: list[ClusterChange] = []
    for c in before_clusters:
        if c.label not in after_labels:
            changes.append(
                ClusterChange(
                    label=c.label,
                    status="resolved",
                    matched_with=None,
                    reason="No longer flagged by personas after the revision.",
                )
            )
    for c in after_clusters:
        if c.label in before_labels:
            changes.append(
                ClusterChange(
                    label=c.label,
                    status="persisting",
                    matched_with=c.label,
                    reason="Still surfaced in persona flags after the revision.",
                )
            )
        else:
            changes.append(
                ClusterChange(
                    label=c.label,
                    status="new",
                    matched_with=None,
                    reason="New issue surfaced by personas on the revised copy.",
                )
            )
    return changes
