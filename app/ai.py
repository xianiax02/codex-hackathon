from __future__ import annotations

from collections.abc import Sequence
from typing import Literal, Optional

from openai import OpenAI, OpenAIError
from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: Optional[SecretStr] = None
    openai_stt_model: str = "gpt-4o-transcribe"
    openai_coach_model: str = "gpt-5.6-luna"

    @property
    def has_openai_key(self) -> bool:
        return bool(
            self.openai_api_key
            and self.openai_api_key.get_secret_value().strip()
        )


class ScoringSlot(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(pattern=r"^[a-z][a-z0-9_]{0,31}$")
    label_zh: str = Field(min_length=1, max_length=60)
    weight: int = Field(ge=1, le=100)


class SceneSlot(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(pattern=r"^[a-z][a-z0-9_]{0,31}$")
    label_zh: str = Field(min_length=1, max_length=60)


def make_scoring_slots(slots: Sequence[SceneSlot]) -> list[ScoringSlot]:
    weights = (50, 50) if len(slots) == 2 else (40, 35, 25)
    return [
        ScoringSlot(id=slot.id, label_zh=slot.label_zh, weight=weight)
        for slot, weight in zip(slots, weights, strict=True)
    ]


class ScenePlan(BaseModel):
    model_config = ConfigDict(frozen=True)

    mission_zh: str
    mission_detail_zh: str
    counterpart_zh: str
    purpose_zh: str
    channel_zh: str
    required_information_zh: list[str] = Field(min_length=1, max_length=3)
    teacher_question_ko: str
    scoring_slots: list[SceneSlot] = Field(min_length=2, max_length=3)

    @model_validator(mode="after")
    def has_complete_scoring_weights(self) -> "ScenePlan":
        if len({slot.id for slot in self.scoring_slots}) != len(self.scoring_slots):
            raise ValueError("scoring slot IDs must be unique")
        return self


class LanguageCorrection(BaseModel):
    model_config = ConfigDict(frozen=True)

    priority: Literal["meaning", "clarity", "politeness", "naturalness"]
    label_ko: str
    spoken_fragment_ko: str
    suggestion_ko: str
    explanation_zh: str


class LanguageFeedback(BaseModel):
    model_config = ConfigDict(frozen=True)

    spoken_ko: str
    corrections: list[LanguageCorrection] = Field(max_length=1)
    target_sentence_ko: str
    covered_slot_ids: list[str] = Field(max_length=3)


class RehearsalAI:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client = OpenAI(
            api_key=settings.openai_api_key.get_secret_value(), timeout=20.0
        )

    def transcribe(self, audio: bytes, content_type: str, language: str) -> Optional[str]:
        try:
            response = self._client.audio.transcriptions.create(
                file=("recording.webm", audio, content_type),
                language=language,
                model=self._settings.openai_stt_model,
            )
        except (OpenAIError, ValidationError):
            return None
        transcript = response.text.strip()
        return transcript or None

    def create_scene(self, situation_transcript: str) -> Optional[ScenePlan]:
        try:
            response = self._client.responses.parse(
                model=self._settings.openai_coach_model,
                instructions=(
                    "You plan one short Korean phone rehearsal for a Mandarin-speaking "
                    "parent. Use only facts in the Chinese situation transcript. Return "
                    "simplified Chinese for all *_zh fields and one polite Korean teacher "
                    "question. Return two or three unique scoring slots in practical "
                    "priority order using snake_case IDs and simplified-Chinese labels. "
                    "Do not output numeric scores or weights, assess pronunciation, or "
                    "invent names, dates, academy policies, fees, refund terms, or "
                    "re-enrollment availability."
                ),
                input=f"Chinese situation transcript: {situation_transcript}",
                text_format=ScenePlan,
            )
        except (OpenAIError, ValidationError):
            return None
        return response.output_parsed

    def coach_language(
        self,
        teacher_question: str,
        transcript: str,
        scoring_slots: list[ScoringSlot],
    ) -> Optional[LanguageFeedback]:
        try:
            response = self._client.responses.parse(
                model=self._settings.openai_coach_model,
                instructions=(
                    "You are a concise Korean phone-call coach for Mandarin speakers. "
                    "Use only the spoken Korean and teacher question. Return at most one "
                    "language correction, preserve the user's meaning, and write the "
                    "explanation in simplified Chinese. Never assess pronunciation, score, "
                    "or claim an error that is absent from the transcript. Return only "
                    "scoring slot IDs whose meaning is explicitly present in the spoken "
                    "Korean; do not create a score or invent academy policies, fees, or "
                    "re-enrollment availability."
                ),
                input=(
                    f"Teacher question: {teacher_question}\n"
                    f"Spoken Korean transcript: {transcript}\n"
                    f"Scoring slots: {[slot.model_dump() for slot in scoring_slots]}"
                ),
                text_format=LanguageFeedback,
            )
        except (OpenAIError, ValidationError):
            return None
        return response.output_parsed
