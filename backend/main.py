#!/usr/bin/env python3
"""
PersonalBranding.com — Analysis API
FastAPI server that runs the research pipeline and returns structured dossier data.

Deploy to Railway / Render / Fly.io, then set VITE_API_URL in Netlify to point here.

Local dev:
    uvicorn backend.main:app --reload --port 8000
    # or from repo root:
    cd backend && uvicorn main:app --reload --port 8000
"""

import sys
import json
import os
import asyncio
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from dotenv import load_dotenv

# Allow importing execution/ scripts
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "execution"))
load_dotenv(ROOT / ".env")

from research import run_research  # noqa: E402

# ---------------------------------------------------------------------------
app = FastAPI(title="PersonalBranding Analysis API", version="1.0.0")

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    name: str
    email: str
    website_url: str  # str instead of HttpUrl for flexibility


class AnalyzeResponse(BaseModel):
    success: bool
    data: dict


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    """
    Run the full research pipeline for a given website URL.
    Returns the structured dossier JSON.
    Takes ~30–90 seconds depending on network speed.
    """
    website_url = req.website_url.strip()
    if not website_url.startswith("http"):
        website_url = "https://" + website_url

    try:
        # run_research is synchronous and CPU/IO bound — run in thread pool
        dossier_path: Path = await asyncio.to_thread(run_research, website_url)
        dossier = json.loads(dossier_path.read_text(encoding="utf-8"))

        # Inject the submitter info into meta for tracking
        dossier.setdefault("meta", {})
        dossier["meta"]["submitter_name"] = req.name
        dossier["meta"]["submitter_email"] = req.email

        return {"success": True, "data": dossier}

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
