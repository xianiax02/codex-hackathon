from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.demo_fixture import attempt_fixture, context_fixture


ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT / "web"

app = FastAPI(title="모두의 한국어", version="0.1.0")


async def require_audio(request: Request) -> bytes:
    content_type = request.headers.get("content-type", "").split(";", 1)[0]
    if not content_type.startswith("audio/"):
        raise HTTPException(status_code=415, detail="audio content-type이 필요합니다")

    audio = await request.body()
    if not audio:
        raise HTTPException(status_code=422, detail="녹음된 audio가 없습니다")
    return audio


@app.get("/api/health")
def health():
    return {"status": "ok", "analysis_mode": "fixture"}


@app.post("/api/context")
async def create_context(request: Request):
    await require_audio(request)
    return JSONResponse(context_fixture())


@app.post("/api/attempts")
async def analyze_attempt(
    request: Request,
    attempt: Literal["first", "retry"] = "first",
    turn: int = Query(1, ge=1, le=3),
):
    await require_audio(request)
    return JSONResponse(attempt_fixture(turn, attempt))


if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
