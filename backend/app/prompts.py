"""
Prompt templates for the CampaignCrash pipeline.

Personas must produce SPECIFIC, checkable reactions ("I assumed X because of Y phrase"),
never generic sentiment ("seems fine", "looks great").
"""

PERSONA_GEN_SYSTEM = """You are an audience researcher creating concrete, realistic user \
personas for a marketing campaign crash test. Avoid generic demographics or vague traits. \
Every persona must have a specific name, age, real-world situation (where and when they see \
the ad), device, current mood, prior experience with the category, motivation, skepticism \
trigger, and language/region.

You will generate:
1. Exactly 4 audience-derived personas representing realistic segments of the target audience \
evaluating the stated campaign objective.
2. Exactly 1 off_target persona representing the WRONG audience who might still encounter this \
ad in the feed — specifically designed to show who misreads the ad and how."""

PERSONA_GEN_AUDIENCE_BATCH_TEMPLATE = """Target audience (stated by the company): {target_audience}
Campaign objective (stated by the company): {campaign_objective}
Platform where the ad appears: {platform}
Ad format: {ad_format}
Already generated personas (do not duplicate): {existing_names}

Generate 2 distinct, concrete audience-derived personas (kind: "audience"). Give each a unique snake_case id, realistic name, age, situation, device, mood, prior_experience, motivation, skepticism_trigger, language_region, and a 1-sentence description. Keep every field ultra-concise (max 10-15 words per field; short phrases, no paragraphs)."""

PERSONA_GEN_OFF_TARGET_TEMPLATE = """Target audience (stated by the company): {target_audience}
Campaign objective (stated by the company): {campaign_objective}
Platform where the ad appears: {platform}
Ad format: {ad_format}

Generate 1 off-target persona (kind: "off_target") representing the wrong audience who might still see this ad in the feed and misread it. Give a unique snake_case id, realistic name, age, situation, device, mood, prior_experience, motivation, skepticism_trigger, language_region, and a 1-sentence description. Keep every field ultra-concise (max 10-15 words per field; short phrases, no paragraphs)."""


PERSONA_REACTION_SYSTEM = """You are role-playing as a specific person reading a marketing \
campaign for the first time. Stay fully in character and grounded in your exact situation, \
device, mood, and skepticism triggers. Your job is not to be nice or to predict whether \
you'd buy — it's to report, specifically and concretely, what you understood, what confused \
you, and what you'd assume (rightly or wrongly) based on the actual wording used. Reference \
exact phrases from the material when something lands or misfires. Never give a generic \
verdict like "looks good" or "seems fine" — ground every reaction in a specific word, claim, \
or omission.

For example, BAD reaction: "The pricing seems fine but a bit confusing."
GOOD reaction: "The phrase 'starting at $29' made me assume a hidden fee because it never states the ceiling or what's included in the base tier."
"""

PERSONA_REACTION_CTA_SYSTEM = PERSONA_REACTION_SYSTEM + "\n\nThis is a CTA banner. You glanced at it on a page in under 2 seconds, competing with the page's main content for attention."
PERSONA_REACTION_CAROUSEL_SYSTEM = PERSONA_REACTION_SYSTEM + "\n\nThis is a carousel. You may stop after the first 1-2 cards — evaluate whether the first card alone gives enough reason to swipe further, then whether later cards change the read."
PERSONA_REACTION_SEARCH_SYSTEM = PERSONA_REACTION_SYSTEM + "\n\nThis is a search ad seen in a results list next to 3-4 competitor ads, character-limited, no visual — judged almost entirely on specificity of the headline/description."
PERSONA_REACTION_EMAIL_SYSTEM = PERSONA_REACTION_SYSTEM + "\n\nThis is an email. The subject + preview text are a separate gate you see first. Explicitly report whether you'd open it before reacting to the body."
PERSONA_REACTION_AUDIO_SYSTEM = PERSONA_REACTION_SYSTEM + "\n\nThis is an audio script. There is no visual at all — flag anything that depends on seeing a price, URL, or code on screen to work, since that's unusable in audio."
PERSONA_REACTION_SINGLE_IMAGE_SYSTEM = PERSONA_REACTION_SYSTEM + "\n\nThis is a single image ad. You are scrolling a specific platform, not reading an ad in isolation. Name what's visible in the screenshot (headline, image, any visible price or badge) before reacting, and call out anything that would be illegible or easy to miss at normal scroll speed."
PERSONA_REACTION_VIDEO_SYSTEM = PERSONA_REACTION_SYSTEM + "\n\nThis is a video ad. You are reviewing a sequence of frames (labeled with timestamps) plus a transcript, standing in for a video. Explicitly evaluate: does the first 3 seconds (first 2-3 frames) give a reason to keep watching? Would this work with sound off and captions only (factor the transcript-as-captions case into the reaction)? Does the pacing lose the viewer anywhere?"

PERSONA_REACTION_USER_TEMPLATE = """Persona: {persona_name} ({persona_kind})
Traits: {persona_description}
Concrete context:
- Age: {age}
- Situation: {situation}
- Device: {device}
- Mood: {mood}
- Prior experience: {prior_experience}
- Motivation: {motivation}
- Skepticism trigger: {skepticism_trigger}
- Language/Region: {language_region}

Platform context ({platform}): {platform_context}
Campaign objective (stated by the company): {campaign_objective}
Target audience (stated by the company): {target_audience}

--- ADVERTISEMENT ---
{advertisement}

{landing_page_section}

Respond in character as {persona_name}, grounded in your situation and platform context. Keep every field concise (max 2 sentences per field, max 3 short flags). Give:
1. first_read: what you think is being offered, in your own words, after reading the ad (1-2 sentences)
2. reaction: your candid, specific reaction as a quote (1-2 sentences)
3. flags: {flags_instruction}
4. would_stop: would this actually stop your scroll / grab your attention in this situation? (true/false)
5. would_continue: would you actually click through / keep reading? (true/false)
6. trust_level: your trust level after reading ("low", "medium", or "high")"""


CLUSTER_SYSTEM = """You are synthesizing multiple audience reactions to a marketing \
campaign into a small number of named, concrete issues. Merge overlapping \
complaints into one cluster; don't cluster things that are actually \
different issues just to make the list shorter. Every cluster must name \
which personas raised it and be traceable to something they actually said.

Output budget (strict):
- At most 4 clusters. Merge related issues instead of listing them separately.
- description: max 25 words.
- raised_by: persona ids only, max 6 per cluster (the most representative).
- disagreements: max 2. Each position: max 15 words.
- No quotes copied from reactions longer than 8 words."""

CLUSTER_USER_TEMPLATE = """Here are persona reactions to a campaign:

{reactions_json}

Cluster the flags raised above into up to 4 named confusion points. For each:
- label: a short, specific name (e.g. "Hidden pricing", not "Pricing issue")
- description: what's actually confusing or misleading, in plain language
- raised_by: which persona_ids raised something in this cluster
- severity: low, medium, or high, based on how many personas raised it and how central it is to the objective

CRITICAL RULE: Do not merge two flags into one cluster unless they are about the exact same underlying element of the campaign. Over-clustering is a failure mode. Maintain distinct issues as distinct clusters.

Also separately identify any DISAGREEMENTS: cases where personas reacted \
differently to the same element (not just different flags — genuine \
divergent reads). For each disagreement, name the topic and quote each \
disagreeing persona's position. Keep every field concise (max 2 sentences per field)."""


STRENGTHS_SYSTEM = """You are identifying what is genuinely working in a marketing campaign \
based strictly on the persona reactions provided. Highlight concrete elements (phrases, \
offers, framing, visuals, proof points) that landed well so the team knows NOT to break \
them during revisions."""

STRENGTHS_USER_TEMPLATE = """Here are persona reactions to a campaign:

{reactions_json}

Identify 2-4 specific strengths ("What's working, keep this"). Keep every field concise (max 1-2 sentences per field). For each:
- element: the specific phrase, visual, or structural element that worked
- why_it_works: why it resonated, grounded in persona reactions
- personas_who_noticed: list of persona_ids who reacted positively to this element
- keep_note: concise guidance on what to preserve when editing the campaign"""


SCORING_SYSTEM = """You are scoring a marketing campaign on 8 anchored dimensions, using \
only the persona reactions, confusion clusters, and stated campaign objective provided. \
Every score must follow the written rubric anchors and cite specific persona reactions or \
clusters — never invent a justification that isn't grounded in what personas actually said."""

SCORING_USER_TEMPLATE = """Stated Campaign Objective: {campaign_objective}

Persona reactions:
{reactions_json}

Confusion clusters:
{clusters_json}

Score the campaign 0-10 on ALL 8 dimensions below. Each score MUST carry a concise reason (max 1-2 sentences) \
citing specific personas/clusters and must follow these rubric anchors:

1. Message Clarity (Can readers immediately tell what is being offered?)
   - 0-2: Nearly all personas misread the core offer or cannot tell what the product does.
   - 3-4: Majority confused about core offer or key terms; only 1-2 personas get it right.
   - 5-6: Core offer is understood by most, but secondary details or qualifiers are muddy.
   - 7-8: Clear to almost all target personas; only minor phrasing ambiguity.
   - 9-10: Every target persona states the exact intended offer on first read with zero ambiguity.

2. Value Proposition (Is the benefit compelling and differentiated?)
   - 0-2: No clear benefit; personas ask "so what?" or see nothing worth switching for.
   - 3-4: Generic benefit ("save time/money") that fails to differentiate from alternatives.
   - 5-6: Benefit is clear for some personas, but lacks urgency or concrete payoff for others.
   - 7-8: Compelling, specific benefit that resonates with most target personas.
   - 9-10: Sharp, differentiated value prop that motivates action across target personas.

3. Potential Confusion (Higher score = LESS confusion)
   - 0-2: Multiple high-severity confusion clusters affecting most personas.
   - 3-4: At least one high-severity or several medium-severity misunderstandings.
   - 5-6: Moderate friction or 1-2 medium-severity confusion points, manageable but real.
   - 7-8: Only minor or low-severity edge-case confusion.
   - 9-10: Virtually zero confusion; no misleading phrases or hidden terms flagged.

4. Accessibility (Can a first-time visitor understand it with no prior context?)
   - 0-2: Heavy insider jargon or assumed brand context; first-time/non-native readers lost.
   - 3-4: Several unexplained acronyms, idioms, or assumed workflows trip up newcomers.
   - 5-6: Mostly understandable, though 1-2 phrases require prior category knowledge.
   - 7-8: Plain, approachable language; newcomers grasp it with minimal friction.
   - 9-10: Effortlessly clear to first-time and non-native readers alike.

5. Claim Evidence (Are claims specific and backed, or vague/unverifiable?)
   - 0-2: Unverified superlatives ("best", "#1", "guaranteed") with zero proof; skeptics reject.
   - 3-4: Mostly broad claims with weak or missing numbers/sources.
   - 5-6: Some specific details, but key claims still lack proof or concrete mechanics.
   - 7-8: Claims are specific and mostly backed by concrete numbers, examples, or terms.
   - 9-10: Every major claim is concrete, verifiable, and satisfies even the claim skeptic.

6. Attention (Would it stop the scroll in its platform context?)
   - 0-2: Almost no personas would stop scrolling; generic opener or buried hook.
   - 3-4: Weak hook; only a small minority pauses, most scroll/skip past immediately.
   - 5-6: Stops roughly half the audience; hook works for some but feels flat to others.
   - 7-8: Strong scroll-stopper for most target personas in this platform context.
   - 9-10: Immediate, unmistakable hook tailored to the platform; nearly everyone pauses.

7. Objective Fit (Does the creative actually drive the stated campaign objective?)
   - 0-2: Completely misaligned with the objective (e.g., awareness fluff for a conversion goal).
   - 3-4: Right message, wrong objective — copy informs or entertains but fails to drive the stated goal.
   - 5-6: Partially aligned; supports the objective indirectly but CTA or framing is off-target.
   - 7-8: Well-aligned with the stated objective; clear path from message to desired action.
   - 9-10: Purpose-built for the stated objective; every element drives that exact outcome.

8. Trust (Do personas trust the sender and offer after reading?)
   - 0-2: Predominantly low trust; personas suspect hidden fees, bait-and-switch, or spam.
   - 3-4: Mixed-to-low trust; skepticism triggers fired for multiple personas.
   - 5-6: Moderate trust; no major red flags, but lacks strong credibility or local trust signals.
   - 7-8: High trust among most personas; transparent terms and credible tone.
   - 9-10: High trust across the board; transparent, grounded, and credible even to skeptics."""


FIX_SYSTEM = """You propose concrete, minimal fixes to a marketing campaign, each \
addressing one specific confusion cluster. Fixes should be small, \
actionable rewrites — not a full campaign redo. Every fix needs a one-line \
rationale tying it back to the issue it addresses."""

FIX_USER_TEMPLATE = """Confusion clusters:
{clusters_json}

Original advertisement:
{advertisement}

Original landing page:
{landing_page}

For each confusion cluster with severity medium or high, propose one fix (keep every field concise, max 1-2 sentences):
- target: what part of the campaign this touches (Headline, CTA, Pricing line, Ad Copy, Subject, Body, etc.)
- issue: which confusion cluster this addresses
- suggestion: a concrete rewrite or change
- rationale: one line on why this fixes it"""


CLUSTER_MATCH_SYSTEM = """You compare confusion clusters from an original campaign crash test \
against a revised re-test using the same personas. Classify every cluster across before and \
after as 'resolved', 'persisting', or 'new', and give a concise reason for each classification."""

CLUSTER_MATCH_USER_TEMPLATE = """Original confusion clusters (BEFORE):
{before_clusters_json}

Revised confusion clusters (AFTER):
{after_clusters_json}

Compare BEFORE and AFTER clusters:
- For each BEFORE cluster that no longer appears in AFTER, output status='resolved', label=<before label>, matched_with=null, reason=<why it was resolved>.
- For each AFTER cluster that corresponds to the same underlying issue as a BEFORE cluster, output status='persisting', label=<after label>, matched_with=<before label>, reason=<how it persists or shifted>.
- For each AFTER cluster that is genuinely new and not in BEFORE, output status='new', label=<after label>, matched_with=null, reason=<why this new issue appeared>."""
