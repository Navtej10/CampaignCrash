import json
import os
import uuid

import groq
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.config import CORS_ORIGINS, MOCK_MODE
from app.engine import (
    get_run,
    retest_campaign,
    retry_analysis_stream,
    run_crash_test,
    run_crash_test_stream,
)
from app.models import CampaignInput, CrashTestResult, RetestRequest, RetestResult
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
    return run_crash_test(campaign)


def _sse_response(stream):
    async def sse_generator():
        try:
            async for event in stream:
                yield f"data: {json.dumps(event)}\n\n"
        except groq.RateLimitError:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Rate limit hit. Wait a minute and retry, or switch model.'})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")


@app.post("/api/crash-test/stream")
async def crash_test_stream(campaign: CampaignInput):
    return _sse_response(run_crash_test_stream(campaign))


@app.post("/api/crash-test/{run_id}/retry-analysis")
async def crash_test_retry_analysis(run_id: str):
    if not get_run(run_id):
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found or expired")
    return _sse_response(retry_analysis_stream(run_id))


@app.post("/api/crash-test/retest", response_model=RetestResult)
def crash_test_retest(payload: RetestRequest):
    try:
        return retest_campaign(payload.run_id, payload.revised_input)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/api/campaigns/upload-video")
async def upload_video(file: UploadFile = File(...)):
    upload_id = str(uuid.uuid4())
    temp_dir = os.path.join(os.getcwd(), "temp_videos")
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, f"{upload_id}_{file.filename}")

    with open(file_path, "wb") as f:
        f.write(await file.read())

    return {"upload_id": upload_id}
