from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json

from app.config import CORS_ORIGINS, MOCK_MODE
from app.engine import run_crash_test, run_crash_test_stream
from app.models import CampaignInput, CrashTestResult
from app.personas import DEFAULT_PERSONAS

app = FastAPI(title="CampaignCrash API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "mock_mode": MOCK_MODE}


@app.get("/api/personas")
def list_personas():
    return DEFAULT_PERSONAS


@app.post("/api/crash-test", response_model=CrashTestResult)
def crash_test(campaign: CampaignInput):
    if not campaign.advertisement.strip():
        raise HTTPException(status_code=400, detail="advertisement is required")
    if not campaign.landing_page and not campaign.landing_page_image:
        raise HTTPException(status_code=400, detail="landing_page or landing_page_image is required")
    return run_crash_test(campaign)


@app.post("/api/crash-test/stream")
async def crash_test_stream(campaign: CampaignInput):
    if not campaign.advertisement.strip():
        raise HTTPException(status_code=400, detail="advertisement is required")
    if not campaign.landing_page and not campaign.landing_page_image:
        raise HTTPException(status_code=400, detail="landing_page or landing_page_image is required")
        
    async def sse_generator():
        async for event in run_crash_test_stream(campaign):
            yield f"data: {json.dumps(event)}\n\n"
            
    return StreamingResponse(sse_generator(), media_type="text/event-stream")
