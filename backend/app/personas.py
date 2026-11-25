from app.models import Persona

# Platform context applied uniformly to every persona during reaction generation.
PLATFORM_CONTEXT: dict[str, str] = {
    "instagram_feed": (
        "Seen in an Instagram Feed while thumb-scrolling between friends' posts and Reels; "
        "visual hierarchy and the first line of caption decide within 1.5 seconds whether you stop."
    ),
    "instagram_story": (
        "Seen in Instagram Stories; you tap through stories in under a second unless the first "
        "frame/hook stops your thumb immediately."
    ),
    "facebook_feed": (
        "Seen in a Facebook Feed mixed with family updates and news; you skim fast and distrust "
        "anything that looks like clickbait or vague engagement bait."
    ),
    "youtube": (
        "Seen on YouTube (pre-roll, in-feed, or thumbnail); you have your finger on 'Skip Ad' "
        "or are scanning thumbnails for clear, non-clickbait value."
    ),
    "google_search": (
        "Seen in Google Search results stacked directly next to 3-4 competing ads and organic "
        "results; judged almost entirely on specificity, numbers, and intent match."
    ),
    "email_inbox": (
        "Seen in a crowded email inbox; subject line and preview text are a separate gate before "
        "you ever open the message, and you delete generic promos on sight."
    ),
    "linkedin_feed": (
        "Seen in a LinkedIn Feed between work updates and industry posts; you evaluate on "
        "professional credibility, concrete ROI, and are put off by empty buzzwords."
    ),
    "other": (
        "Seen in a busy digital feed or page alongside competing content; you give it at most a "
        "2-second glance before deciding whether to engage."
    ),
}


# Fixed contrast personas always included alongside generated audience personas and off_target.
FIXED_CONTRAST_PERSONAS: list[Persona] = [
    Persona(
        id="first_time_customer",
        name="First-time customer",
        kind="contrast",
        description=(
            "Has zero context on the brand or category, needs the value "
            "proposition explained in plain language, easily lost by "
            "insider jargon or unexplained acronyms."
        ),
        age=31,
        situation="Browsing on a break, encountering this brand for the very first time",
        device="Mobile phone",
        mood="Curious but impatient",
        prior_experience="None with this brand or category jargon",
        motivation="Understand what this actually is and whether it solves a real need",
        skepticism_trigger="Unexplained acronyms, insider buzzwords, or assumed context",
        language_region="English (General)",
    ),
    Persona(
        id="price_sensitive",
        name="Price-sensitive buyer",
        kind="contrast",
        description=(
            "Looks for the price before anything else, treats vague or "
            "hidden pricing as a red flag, assumes the worst about "
            "'starting at' language."
        ),
        age=27,
        situation="Scrolling at night while comparing budget options",
        device="Mobile phone",
        mood="Guarded and budget-conscious",
        prior_experience="Burned by hidden subscription fees before",
        motivation="Find out the real total cost upfront before investing time",
        skepticism_trigger="Missing price, 'starting at' caveats, or 'free trial' without clear terms",
        language_region="English (General)",
    ),
    Persona(
        id="claim_skeptic",
        name="Claim skeptic",
        kind="contrast",
        description=(
            "Immediately distrusts superlatives like 'best', '#1', 'guaranteed', "
            "or 'proven' unless backed by specific numbers, methodology, or verifiable proof."
        ),
        age=42,
        situation="Skimming during lunch, hyper-alert to marketing hype",
        device="Desktop browser",
        mood="Analytical and cynical",
        prior_experience="Familiar with category marketing tropes and inflated claims",
        motivation="See concrete evidence or specific mechanics rather than adjectives",
        skepticism_trigger="Words like 'best', '#1', 'guaranteed', or vague percentages without a source",
        language_region="English (General)",
    ),
    Persona(
        id="competitor_loyalist",
        name="Competitor loyalist",
        kind="contrast",
        description=(
            "Already uses and likes an established alternative; asks 'why would I switch "
            "from what I already use?' and needs a clear differentiation or switching incentive."
        ),
        age=35,
        situation="Seeing the ad while already satisfied with a competing product",
        device="Mobile phone",
        mood="Indifferent unless shown a clear edge",
        prior_experience="Active daily user of a well-known competitor",
        motivation="Only switch if there is a clear, low-friction advantage over current tool",
        skepticism_trigger="Generic benefits that their current product already does",
        language_region="English (General)",
    ),
]


def build_language_lens_persona(target_audience: str) -> Persona:
    """Build the language_lens contrast persona parameterized by the audience's region/language."""
    audience_hint = target_audience.strip() or "general global audience"
    return Persona(
        id="language_lens",
        name="Language & local-trust lens",
        kind="contrast",
        description=(
            f"Non-native or regional reader evaluating from the context of '{audience_hint}'. "
            "Mobile-first, reads literally, tripped up by idioms/slang, and looks for local "
            "trust signals (currency, regional availability, clear plain phrasing)."
        ),
        age=29,
        situation=f"Reading on mobile while commuting, evaluating fit for ({audience_hint})",
        device="Mid-range Android phone on cellular data",
        mood="Focused, literal reader",
        prior_experience="Uses mobile-first tools; cautious of foreign/unfamiliar brands",
        motivation="Verify it works in their region/language with clear, literal terms",
        skepticism_trigger="Idioms, US-centric assumptions, missing currency/region clarity, dense text",
        language_region=f"Non-native / regional lens ({audience_hint})",
    )


# Backward-compatible alias for any callers importing DEFAULT_PERSONAS.
DEFAULT_PERSONAS: list[Persona] = FIXED_CONTRAST_PERSONAS + [build_language_lens_persona("")]
