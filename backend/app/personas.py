from app.models import Persona

# Default persona roster. Keep this editable at the API layer later —
# for the scaffold, six fixed personas is enough to demo disagreement.
DEFAULT_PERSONAS: list[Persona] = [
    Persona(
        id="student",
        name="Student",
        description=(
            "Cash-strapped, skims fast, decides in seconds, compares against "
            "free or near-free alternatives, distrusts anything that looks "
            "like a subscription trap."
        ),
    ),
    Persona(
        id="parent",
        name="Parent",
        description=(
            "Time-poor, reading on a phone between tasks, wants to know "
            "immediately whether this solves a specific problem for their "
            "family, has low tolerance for vague copy."
        ),
    ),
    Persona(
        id="professional",
        name="Professional",
        description=(
            "Evaluates on credibility and ROI, reads the fine print, "
            "compares against tools they already pay for, put off by "
            "hype-y language or unverified claims."
        ),
    ),
    Persona(
        id="price_sensitive",
        name="Price-sensitive buyer",
        description=(
            "Looks for the price before anything else, treats vague or "
            "hidden pricing as a red flag, assumes the worst about "
            "'starting at' language."
        ),
    ),
    Persona(
        id="first_time_customer",
        name="First-time customer",
        description=(
            "Has zero context on the brand or category, needs the value "
            "proposition explained in plain language, easily lost by "
            "insider jargon or unexplained acronyms."
        ),
    ),
    Persona(
        id="existing_customer",
        name="Existing customer",
        description=(
            "Already knows the brand, is scanning for what's new or "
            "different this time, annoyed by messaging that re-explains "
            "basics they already know."
        ),
    ),
]
