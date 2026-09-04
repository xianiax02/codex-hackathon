from typing import Literal

from openai import OpenAI, OpenAIError
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: SecretStr | None = None
    openai_stt_model: str = "gpt-4o-transcribe"
    openai_coach_model: str = "gpt-5.6-luna"

    @property
    def has_openai_key(self) -> bool:
        return bool(
            self.openai_api_key
            and self.openai_api_key.get_secret_value().strip()
        )


class ScenePlan(BaseModel):
    mission_zh: str
    mission_detail_zh: str
    counterpart_zh: str
    purpose_zh: str
    channel_zh: str
    required_information_zh: list[str] = Field(min_length=1, max_length=3)
    teacher_question_ko: str


class LanguageCorrection(BaseModel):
    priority: Literal["meaning", "clarity", "politeness", "naturalness"]
    label_ko: str
    spoken_fragment_ko: str
    suggestion_ko: str
    explanation_zh: str


class LanguageFeedback(BaseModel):
    spoken_ko: str
    corrections: list[LanguageCorrection] = Field(max_length=1)
    target_sentence_ko: str


class RehearsalAI:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client = OpenAI(
            api_key=settings.openai_api_key.get_secret_value(), timeout=20.0
        )

    def transcribe(self, audio: bytes, content_type: str, language: str) -> str | None:
        try:
            response = self._client.audio.transcriptions.create(
                file=("recording.webm", audio, content_type),
                language=language,
                model=self._settings.openai_stt_model,
            )
        except OpenAIError:
            return None
        transcript = response.text.strip()
        return transcript or None

    def create_scene(self, situation_transcript: str) -> ScenePlan | None:
        try:
            response = self._client.responses.parse(
                model=self._settings.openai_coach_model,
                instructions=(
                    "You plan one short Korean phone rehearsal for a Mandarin-speaking "
                    "parent. Use only facts in the Chinese situation transcript. Return "
                    "simplified Chinese for all *_zh fields and one polite Korean teacher "
                    "question. Do not score pronunciation or invent names, dates, or facts."
                ),
                input=f"Chinese situation transcript: {situation_transcript}",
                text_format=ScenePlan,
            )
        except OpenAIError:
            return None
        return response.output_parsed

    def coach_language(
        self, teacher_question: str, transcript: str
    ) -> LanguageFeedback | None:
        try:
            response = self._client.responses.parse(
                model=self._settings.openai_coach_model,
                instructions=(
                    "You are a concise Korean phone-call coach for Mandarin speakers. "
                    "Use only the spoken Korean and teacher question. Return at most one "
                    "language correction, preserve the user's meaning, and write the "
                    "explanation in simplified Chinese. Never assess pronunciation, score, "
                    "or claim an error that is absent from the transcript."
                ),
                input=(
                    f"Teacher question: {teacher_question}\n"
                    f"Spoken Korean transcript: {transcript}"
                ),
                text_format=LanguageFeedback,
            )
        except OpenAIError:
            return None
        return response.output_parsed
