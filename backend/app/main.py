from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json

from app.config import CORS_ORIGINS, MOCK_MODE
from app.engine import run_crash_test, run_crash_test_stream
from app.models import CampaignInput, CrashTestResult
from app.personas import DEFAULT_PERSONAS
from fastapi import File, UploadFile
import uuid
import os
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


@app.post("/api/crash-test/stream")
async def crash_test_stream(campaign: CampaignInput):
    async def sse_generator():
        async for event in run_crash_test_stream(campaign):
            yield f"data: {json.dumps(event)}\n\n"
            
    return StreamingResponse(sse_generator(), media_type="text/event-stream")

@app.post("/api/campaigns/upload-video")
async def upload_video(file: UploadFile = File(...)):
    upload_id = str(uuid.uuid4())
    temp_dir = os.path.join(os.getcwd(), "temp_videos")
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, f"{upload_id}_{file.filename}")
    
    with open(file_path, "wb") as f:
        f.write(await file.read())
        
    return {"upload_id": upload_id}
