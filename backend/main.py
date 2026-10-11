#!/usr/bin/env python3
"""
PersonalBranding.com — Analysis API (Modal deployment)

Deploy:
    modal token new                          # one-time auth
    modal secret create personalbranding-secrets \\
        OPENAI_API_KEY=sk-... \\
        FIRECRAWL_API_KEY=fc-... \\
        SERPAPI_API_KEY=...
    modal deploy backend/main.py

Local dev (still works — just run uvicorn directly):
    uvicorn backend.main:web_app --port 8000 --reload
"""

from pathlib import Path
import sys
import json

import modal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# ── Paths ────────────────────────────────────────────────────────────────────

REPO_ROOT      = Path(__file__).parent.parent
EXECUTION_DIR  = REPO_ROOT / "execution"

# ── Modal app ────────────────────────────────────────────────────────────────

app = modal.App("personalbranding-api")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install([
        "fastapi[standard]>=0.111.0",
        "openai>=1.30.0",
        "firecrawl-py>=1.0.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
    ])
    # Ensure the .tmp dir exists inside the container
    .run_commands("mkdir -p /root/.tmp")
    # Copy execution/ scripts into /root/execution inside the container
    # add_local_dir must come last; copy=True bakes files into the image layer
    .add_local_dir(
        EXECUTION_DIR,
        remote_path="/root/execution",
        copy=True,
    )
)

# ── FastAPI app ───────────────────────────────────────────────────────────────

web_app = FastAPI(title="PersonalBranding Analysis API", version="2.0.0")

web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    name: str
    email: str
    website_url: str


@web_app.get("/health")
def health():
    return {"status": "ok"}


@web_app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    import asyncio

    # On Modal the execution scripts live at /root/execution.
    # Locally they're at EXECUTION_DIR (repo root / execution).
    for candidate in ("/root/execution", str(EXECUTION_DIR)):
        if candidate not in sys.path and Path(candidate).exists():
            sys.path.insert(0, candidate)

    from research import run_research  # noqa: PLC0415

    url = req.website_url.strip()
    if not url.startswith("http"):
        url = "https://" + url

    try:
        dossier_path: Path = await asyncio.to_thread(run_research, url)
        dossier = json.loads(dossier_path.read_text(encoding="utf-8"))
        dossier.setdefault("meta", {})
        dossier["meta"]["submitter_name"]  = req.name
        dossier["meta"]["submitter_email"] = req.email
        return {"success": True, "data": dossier}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── Modal entrypoint ──────────────────────────────────────────────────────────

@app.function(
    image=image,
    secrets=[modal.Secret.from_name("personalbranding-secrets")],
    timeout=300,            # 5 min — research pipeline can take ~90 s
)
@modal.concurrent(max_inputs=20)
@modal.asgi_app()
def fastapi_app():
    return web_app
