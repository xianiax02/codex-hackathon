from fastapi.testclient import TestClient

from app import main
from app.ai import LanguageCorrection, LanguageFeedback, ScenePlan


class FakeRehearsalAI:
    def transcribe(self, audio: bytes, content_type: str, language: str) -> str:
        if language == "zh":
            return "孩子从下个月开始停两个月的课，之后想继续上课。"
        if audio == b"retry":
            return "다음 달부터 두 달 동안 아이 학원을 쉬고 싶어요"
        return "다음 달부터 아이 학원 두 달 쉬고 싶어요"

    def create_scene(self, situation_transcript: str) -> ScenePlan:
        return ScenePlan(
            mission_zh="和补习班商量暂停两个月后再上课",
            mission_detail_zh="说明开始时间、暂停时长，并询问重新上课前何时联系。",
            counterpart_zh="补习班老师",
            purpose_zh="暂停上课与重新报名咨询",
            channel_zh="电话",
            required_information_zh=["下个月开始", "暂停两个月", "之后想重新上课"],
            teacher_question_ko="언제부터 얼마나 쉬실 예정인가요?",
        )

    def coach_language(
        self, teacher_question: str, transcript: str
    ) -> LanguageFeedback:
        return LanguageFeedback(
            spoken_ko=transcript,
            corrections=[
                LanguageCorrection(
                    priority="politeness",
                    label_ko="더 공손하게 말해요",
                    spoken_fragment_ko="아이 학원 두 달",
                    suggestion_ko="두 달 동안 아이 학원을",
                    explanation_zh="加上‘동안’，能清楚表达暂停上课的时间长度。",
                )
            ],
            target_sentence_ko="다음 달부터 두 달 동안 아이 학원을 쉬고 싶어요.",
        )


def test_live_first_round_keeps_the_partner_frontend_contract(monkeypatch):
    monkeypatch.setattr(main, "rehearsal_ai", FakeRehearsalAI())
    client = TestClient(main.app)

    context = client.post(
        "/api/context", content=b"audio", headers={"content-type": "audio/webm"}
    )

    assert context.status_code == 200
    assert context.json()["analysis_mode"] == "live"
    assert context.json()["source_transcript"].startswith("孩子")
    assert context.json()["max_turns"] == 3
    assert len(context.json()["turn_plan"]) == 3
    assert context.json()["turn_plan"][1]["teacher_question_ko"] == (
        "학원을 그만두는 건가요, 잠시 쉬는 건가요?"
    )
    assert context.json()["turn_plan"][2]["teacher_question_ko"] == (
        "다시 시작하는 것에 대해 궁금한 점이 있으세요?"
    )

    first = client.post(
        "/api/attempts?attempt=first&turn=1&teacher_question=안녕하세요",
        content=b"audio",
        headers={"content-type": "audio/webm"},
    )

    assert first.status_code == 200
    assert first.json()["analysis_mode"] == "live"
    assert first.json()["feedback"]["pronunciation"]["score"] == 100
    assert first.json()["target_sentence"] == "다음 달부터 두 달 동안 아이 학원을 쉬고 싶어요."

    retry = client.post(
        "/api/attempts?attempt=retry&turn=1&target_sentence=다음 달부터 두 달 동안 아이 학원을 쉬고 싶어요.&previous_score=100",
        content=b"retry",
        headers={"content-type": "audio/webm"},
    )

    assert retry.status_code == 200
    assert retry.json()["comparison"] == {"before": 100, "after": 100}
    assert retry.json()["tomorrow_card"]["sentences"] == [
        "다음 달부터 두 달 동안 아이 학원을 쉬고 싶어요."
    ]
