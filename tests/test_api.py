from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_reports_fixture_mode():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "analysis_mode": "fixture"}


def test_empty_context_audio_is_rejected():
    response = client.post(
        "/api/context", content=b"", headers={"content-type": "audio/webm"}
    )

    assert response.status_code == 422


def test_non_audio_context_is_rejected():
    response = client.post(
        "/api/context", content=b"hello", headers={"content-type": "text/plain"}
    )

    assert response.status_code == 415


def test_context_audio_returns_rehearsal_scene():
    response = client.post(
        "/api/context", content=b"audio", headers={"content-type": "audio/webm"}
    )

    assert response.status_code == 200
    assert response.json()["teacher_question"] == "안녕하세요. 무슨 일로 연락 주셨나요?"
    assert response.json()["analysis_mode"] == "fixture"
    assert response.json()["max_turns"] == 3
    assert len(response.json()["turn_plan"]) == 3


def test_first_attempt_returns_two_feedback_axes():
    response = client.post(
        "/api/attempts?attempt=first",
        content=b"audio",
        headers={"content-type": "audio/webm"},
    )

    assert response.status_code == 200
    assert set(response.json()["feedback"]) == {"language", "pronunciation"}
    assert response.json()["feedback"]["pronunciation"]["score"] == 68


def test_retry_returns_same_sentence_comparison():
    response = client.post(
        "/api/attempts?attempt=retry",
        content=b"audio",
        headers={"content-type": "audio/webm"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["comparison"] == {"before": 68, "after": 76}
    assert len(body["tomorrow_card"]["sentences"]) == 3


def test_each_planned_turn_has_a_distinct_question():
    questions = []
    for turn in (1, 2, 3):
        response = client.post(
            f"/api/attempts?attempt=first&turn={turn}",
            content=b"audio",
            headers={"content-type": "audio/webm"},
        )
        assert response.status_code == 200
        questions.append(response.json()["teacher_question"])

    assert len(set(questions)) == 3


def test_turn_outside_script_scope_is_rejected():
    response = client.post(
        "/api/attempts?attempt=first&turn=4",
        content=b"audio",
        headers={"content-type": "audio/webm"},
    )

    assert response.status_code == 422
