import pytest
from pydantic import ValidationError

from app.ai import ScenePlan, SceneSlot, ScoringSlot, make_scoring_slots
from app.scoring import retry_score, semantic_slot_score


def test_semantic_slot_score_counts_only_known_covered_slots():
    slots = [
        ScoringSlot(id="absence", label_zh="缺席", weight=40),
        ScoringSlot(id="reason", label_zh="原因", weight=35),
        ScoringSlot(id="next_step", label_zh="下一步", weight=25),
    ]

    assert semantic_slot_score(slots, {"absence", "unknown"}) == 40


def test_scene_plan_rejects_duplicate_slot_ids():
    with pytest.raises(ValidationError):
        ScenePlan(
            mission_zh="请假",
            mission_detail_zh="说明缺席",
            counterpart_zh="老师",
            purpose_zh="请假",
            channel_zh="电话",
            required_information_zh=["缺席"],
            teacher_question_ko="무슨 일로 연락 주셨나요?",
            scoring_slots=[
                SceneSlot(id="absence", label_zh="缺席"),
                SceneSlot(id="absence", label_zh="原因"),
            ],
        )


def test_scene_slots_receive_server_owned_weights_in_priority_order():
    slots = make_scoring_slots(
        [
            SceneSlot(id="absence", label_zh="缺席"),
            SceneSlot(id="reason", label_zh="原因"),
            SceneSlot(id="next_step", label_zh="下一步"),
        ]
    )

    assert [slot.weight for slot in slots] == [40, 35, 25]


def test_retry_score_compares_only_normalized_hangul_syllables():
    assert retry_score("학교에 가지 못합니다.", "학교에 가지 못합니다") == 100
    assert retry_score("가", "나") == 0
