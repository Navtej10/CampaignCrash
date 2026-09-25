import os

from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
CAMPAIGNCRASH_MODEL = os.getenv("CAMPAIGNCRASH_MODEL", "qwen-2.5-32b")
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

# Mock mode is automatic whenever no API key is configured, so the frontend
# can be built and demoed before any model wiring is in place.
MOCK_MODE = not GROQ_API_KEY
