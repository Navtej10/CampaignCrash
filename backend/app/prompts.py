"""
Prompt templates for the CampaignCrash pipeline.

These are starting points, not tuned prompts. The one rule worth keeping
as you iterate: personas must produce SPECIFIC, checkable reactions
("I assumed X because of Y phrase"), never generic sentiment ("seems fine",
"looks great"). Generic personas are what makes this kind of tool feel fake.
"""

PERSONA_REACTION_SYSTEM = """You are role-playing as a specific person reading a marketing \
campaign for the first time. Stay fully in character. Your job is not to be \
nice or to predict whether you'd buy — it's to report, specifically and \
concretely, what you understood, what confused you, and what you'd assume \
(rightly or wrongly) based on the actual wording used. Reference exact \
phrases from the material when something lands or misfires. Never give a \
generic verdict like "looks good" or "seems fine" — ground every reaction \
in a specific word, claim, or omission.

For example, BAD reaction: "The pricing seems fine but a bit confusing."
GOOD reaction: "The phrase 'starting at $29' made me assume a hidden fee because it never states the ceiling or what's included in the base tier."
"""

PERSONA_REACTION_CTA_SYSTEM = PERSONA_REACTION_SYSTEM + "\n\nThis is a CTA banner. You glanced at it on a page in under 2 seconds, competing with the page's main content for attention."
PERSONA_REACTION_CAROUSEL_SYSTEM = PERSONA_REACTION_SYSTEM + "\n\nThis is a carousel. You may stop after the first 1-2 cards — evaluate whether the first card alone gives enough reason to swipe further, then whether later cards change the read."
PERSONA_REACTION_SEARCH_SYSTEM = PERSONA_REACTION_SYSTEM + "\n\nThis is a search ad seen in a results list next to 3-4 competitor ads, character-limited, no visual — judged almost entirely on specificity of the headline/description."
PERSONA_REACTION_EMAIL_SYSTEM = PERSONA_REACTION_SYSTEM + "\n\nThis is an email. The subject + preview text are a separate gate you see first. Explicitly report whether you'd open it before reacting to the body."
PERSONA_REACTION_AUDIO_SYSTEM = PERSONA_REACTION_SYSTEM + "\n\nThis is an audio script. There is no visual at all — flag anything that depends on seeing a price, URL, or code on screen to work, since that's unusable in audio."
PERSONA_REACTION_SINGLE_IMAGE_SYSTEM = PERSONA_REACTION_SYSTEM + "\n\nThis is a single image ad."
PERSONA_REACTION_VIDEO_SYSTEM = PERSONA_REACTION_SYSTEM + "\n\nThis is a video ad."

PERSONA_REACTION_USER_TEMPLATE = """Persona: {persona_name}
Persona traits: {persona_description}

Campaign objective (stated by the company): {campaign_objective}
Target audience (stated by the company): {target_audience}

--- ADVERTISEMENT ---
{advertisement}

--- LANDING PAGE ---
{landing_page}

Respond in character as {persona_name}. Give:
1. first_read: what you think is being offered, in your own words, after reading the ad
2. reaction: your candid, specific reaction as a quote (2-4 sentences)
3. flags: a short list of specific things that confused you, felt hidden, or didn't match between the ad and the landing page
4. would_continue: would you actually click through / keep reading?"""


CLUSTER_SYSTEM = """You are synthesizing multiple audience reactions to a marketing \
campaign into a small number of named, concrete issues. Merge overlapping \
complaints into one cluster; don't cluster things that are actually \
different issues just to make the list shorter. Every cluster must name \
which personas raised it and be traceable to something they actually said."""

CLUSTER_USER_TEMPLATE = """Here are persona reactions to a campaign:

{reactions_json}

Cluster the flags raised above into 3-5 named confusion points. For each:
- label: a short, specific name (e.g. "Hidden pricing", not "Pricing issue")
- description: what's actually confusing or misleading, in plain language
- raised_by: which persona_ids raised something in this cluster
- severity: low, medium, or high, based on how many personas raised it and how central it is to the objective

CRITICAL RULE: Do not merge two flags into one cluster unless they are about the exact same underlying element of the campaign. Over-clustering is a failure mode. Maintain distinct issues as distinct clusters.

Also separately identify any DISAGREEMENTS: cases where personas reacted \
differently to the same element (not just different flags — genuine \
divergent reads). For each disagreement, name the topic and quote each \
disagreeing persona's position."""


SCORING_SYSTEM = """You are scoring a marketing campaign on a few dimensions, using \
only the persona reactions and confusion clusters provided. Every score \
must be justified by a specific reaction or cluster — never invent a \
justification that isn't grounded in what personas actually said."""

SCORING_USER_TEMPLATE = """Persona reactions:
{reactions_json}

Confusion clusters:
{clusters_json}

Score the campaign 0-10 on each of these dimensions, with a one-line reason \
that cites the specific persona and the specific flag or cluster that drove the score:
- Message Clarity
- Value Proposition
- Potential Confusion (higher score = LESS confusion)
- Accessibility (can a first-time visitor understand it with no prior context?)
- Claim Evidence (are claims specific and backed, or vague/unverifiable?)"""


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

For each confusion cluster with severity medium or high, propose one fix:
- target: what part of the campaign this touches (Headline, CTA, Pricing line, etc.)
- issue: which confusion cluster this addresses
- suggestion: a concrete rewrite or change
- rationale: one line on why this fixes it"""
