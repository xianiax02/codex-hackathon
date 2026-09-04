from fastapi.testclient import TestClient

from app import main
from app.ai import LanguageCorrection, LanguageFeedback, ScenePlan


class FakeRehearsalAI:
    def transcribe(self, audio: bytes, content_type: str, language: str) -> str:
        if language == "zh":
            return "孩子明天生病不能上学，要给老师打电话。"
        if audio == b"retry":
            return "아이가 아파서 내일 학교에 가지 못합니다"
        return "아이 아파서 내일 학교 못 가요"

    def create_scene(self, situation_transcript: str) -> ScenePlan:
        return ScenePlan(
            mission_zh="告诉老师孩子明天因病缺席",
            mission_detail_zh="说明孩子生病和明天缺席。",
            counterpart_zh="班主任老师",
            purpose_zh="请假联系",
            channel_zh="电话",
            required_information_zh=["孩子明天缺席", "生病"],
            teacher_question_ko="안녕하세요. 무슨 일로 연락 주셨나요?",
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
                    spoken_fragment_ko="학교 못 가요",
                    suggestion_ko="학교에 가지 못합니다",
                    explanation_zh="对老师说明缺席时，这样说更礼貌。",
                )
            ],
            target_sentence_ko="아이가 아파서 내일 학교에 가지 못합니다.",
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
    assert context.json()["max_turns"] == 1

    first = client.post(
        "/api/attempts?attempt=first&turn=1&teacher_question=안녕하세요",
        content=b"audio",
        headers={"content-type": "audio/webm"},
    )

    assert first.status_code == 200
    assert first.json()["analysis_mode"] == "live"
    assert first.json()["feedback"]["pronunciation"]["score"] == 100
    assert first.json()["target_sentence"] == "아이가 아파서 내일 학교에 가지 못합니다."

    retry = client.post(
        "/api/attempts?attempt=retry&turn=1&target_sentence=아이가 아파서 내일 학교에 가지 못합니다.&previous_score=100",
        content=b"retry",
        headers={"content-type": "audio/webm"},
    )

    assert retry.status_code == 200
    assert retry.json()["comparison"] == {"before": 100, "after": 100}
    assert retry.json()["tomorrow_card"]["sentences"] == [
        "아이가 아파서 내일 학교에 가지 못합니다."
    ]
