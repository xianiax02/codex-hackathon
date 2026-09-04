from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import TypeAdapter, ValidationError

from app.ai import RehearsalAI, ScoringSlot, Settings, make_scoring_slots
from app.demo_fixture import TURN_PLAN, attempt_fixture, context_fixture
from app.scoring import (
    missing_target_words,
    pronunciation_status,
    retry_score,
    semantic_slot_score,
)


ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT / "web"

app = FastAPI(title="모두의 한국어", version="0.1.0")
settings = Settings()
rehearsal_ai = RehearsalAI(settings) if settings.has_openai_key else None
scoring_slots_adapter = TypeAdapter(list[ScoringSlot])


async def require_audio(request: Request) -> bytes:
    content_type = request.headers.get("content-type", "").split(";", 1)[0]
    if not content_type.startswith("audio/"):
        raise HTTPException(status_code=415, detail="audio content-type이 필요합니다")

    audio = await request.body()
    if not audio:
        raise HTTPException(status_code=422, detail="녹음된 audio가 없습니다")
    return audio


def parse_scoring_slots(raw_slots: str | None) -> list[ScoringSlot] | None:
    if raw_slots is None:
        return None
    try:
        slots = scoring_slots_adapter.validate_json(raw_slots)
    except ValidationError:
        return None
    return slots if sum(slot.weight for slot in slots) == 100 else None


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "analysis_mode": "live" if rehearsal_ai else "fixture",
    }


@app.post("/api/context")
async def create_context(request: Request):
    audio = await require_audio(request)
    if not rehearsal_ai:
        return JSONResponse(context_fixture())

    content_type = request.headers.get("content-type", "audio/webm").split(";", 1)[0]
    transcript = rehearsal_ai.transcribe(audio, content_type, "zh")
    if not transcript:
        return JSONResponse(context_fixture())

    scene = rehearsal_ai.create_scene(transcript)
    if not scene:
        return JSONResponse(context_fixture())

    return JSONResponse(
        {
            "analysis_mode": "live",
            "source_transcript": transcript,
            "mission": scene.mission_zh,
            "mission_detail": scene.mission_detail_zh,
            "counterpart": scene.counterpart_zh,
            "purpose": scene.purpose_zh,
            "channel": scene.channel_zh,
            "required_information": scene.required_information_zh,
            "scoring_slots": [
                slot.model_dump() for slot in make_scoring_slots(scene.scoring_slots)
            ],
            "max_turns": 3,
            "turn_plan": [
                {
                    "turn": 1,
                    "objective_zh": scene.mission_zh,
                    "teacher_question_ko": scene.teacher_question_ko,
                },
                *TURN_PLAN[1:],
            ],
            "teacher_question": scene.teacher_question_ko,
        }
    )


@app.post("/api/attempts")
async def analyze_attempt(
    request: Request,
    attempt: Literal["first", "retry"] = "first",
    turn: int = Query(1, ge=1, le=3),
    teacher_question: Optional[str] = Query(None, max_length=200),
    target_sentence: Optional[str] = Query(None, max_length=300),
    previous_score: Optional[int] = Query(None, ge=0, le=100),
    scoring_slots: Optional[str] = Query(None, max_length=1000),
):
    audio = await require_audio(request)
    if not rehearsal_ai or turn != 1:
        return JSONResponse(attempt_fixture(turn, attempt))

    content_type = request.headers.get("content-type", "audio/webm").split(";", 1)[0]
    transcript = rehearsal_ai.transcribe(audio, content_type, "ko")
    if not transcript:
        return JSONResponse(attempt_fixture(turn, attempt))

    question = teacher_question or TURN_PLAN[turn - 1]["teacher_question_ko"]
    if attempt == "retry":
        if target_sentence is None or previous_score is None:
            return JSONResponse(attempt_fixture(turn, attempt))
        score = retry_score(target_sentence, transcript)
        focus_words = missing_target_words(target_sentence, transcript)
        return JSONResponse(
            {
                "analysis_mode": "live",
                "phase": "turn_review",
                "turn": turn,
                "teacher_question": question,
                "transcript": transcript,
                "target_sentence": target_sentence,
                "comparison": {"before": previous_score, "after": score},
                "feedback": {
                    "language": {
                        "priority": "意思传达清楚了",
                        "said": transcript,
                        "target": target_sentence,
                        "explanation": "这次根据实际语音转写重新计算了句子传达度。",
                    },
                    "pronunciation": {
                        "score": score,
                        "status": pronunciation_status(score),
                        "focus_word": " · ".join(focus_words),
                        "guide": (
                            "可以保持刚才的速度。"
                            if not focus_words
                            else f"请再清楚地说“{focus_words[0]}”。"
                        ),
                    },
                },
                "tomorrow_card": {
                    "sentences": [target_sentence],
                    "expected_question": question,
                    "learned": "这句已经可以用于实际通话。",
                },
            }
        )

    slots = parse_scoring_slots(scoring_slots)
    if slots is None:
        return JSONResponse(attempt_fixture(turn, attempt))

    feedback = rehearsal_ai.coach_language(question, transcript, slots)
    if not feedback:
        return JSONResponse(attempt_fixture(turn, attempt))

    correction = feedback.corrections[0] if feedback.corrections else None
    target = feedback.target_sentence_ko.strip() or transcript
    covered_slot_ids = set(feedback.covered_slot_ids)
    score = semantic_slot_score(slots, covered_slot_ids)
    return JSONResponse(
        {
            "analysis_mode": "live",
            "phase": "feedback",
            "turn": turn,
            "teacher_question": question,
            "transcript": transcript,
            "target_sentence": target,
            "feedback": {
                "language": {
                    "priority": correction.label_ko if correction else "의미 전달 확인",
                    "said": feedback.spoken_ko,
                    "target": target,
                    "explanation": (
                        correction.explanation_zh
                        if correction
                        else "这句话的关键信息已经表达清楚。"
                    ),
                },
                "pronunciation": {
                    "score": score,
                    "status": pronunciation_status(score),
                    "focus_word": "",
                    "guide": "这是基于语音转写的句子传达度，不是音素判定。",
                },
            },
        }
    )


if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
