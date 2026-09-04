from copy import deepcopy


TURN_PLAN = [
    {"turn": 1, "objective_zh": "确认家长身份和缺席事实", "teacher_question_ko": "안녕하세요. 무슨 일로 연락 주셨나요?"},
    {"turn": 2, "objective_zh": "确认孩子现在的状态", "teacher_question_ko": "민수는 지금 어떤 상태인가요?"},
    {"turn": 3, "objective_zh": "确认返校和再次联系计划", "teacher_question_ko": "언제 다시 등교할 수 있을까요?"},
]

TURN_CONTENT = {
    1: {
        "spoken": "선생님, 민수가 아파서 내일 학교 못 갑니다.",
        "target": "선생님, 민수가 아파서 내일 학교에 가지 못합니다.",
        "priority": "更礼貌地说",
        "explanation": "用‘학교에 가지 못합니다’能更清楚、礼貌地说明缺席。",
        "focus": "못 갑니다",
        "guide": "‘못 갑니다’慢一点连起来说。",
        "first_score": 68,
        "retry_score": 76,
    },
    2: {
        "spoken": "민수가 열 조금 있어요.",
        "target": "민수가 열이 조금 나요.",
        "priority": "句子更完整",
        "explanation": "加上助词‘이’，并用‘열이 나요’说明发烧更自然。",
        "focus": "열이",
        "guide": "‘열-이’不要断开，轻轻连起来说。",
        "first_score": 73,
        "retry_score": 82,
    },
    3: {
        "spoken": "내일 보고 다시 연락해요.",
        "target": "내일 상태를 보고 다시 연락드리겠습니다.",
        "priority": "更礼貌地说",
        "explanation": "‘연락드리겠습니다’更礼貌，也能说明下一步。",
        "focus": "연락드리겠습니다",
        "guide": "长句分成‘연락-드리겠습니다’两段练习。",
        "first_score": 80,
        "retry_score": 87,
    },
}


def context_fixture():
    return deepcopy({
        "analysis_mode": "fixture",
        "source_transcript": "明天孩子发烧，不能去学校。我需要给班主任打电话。",
        "mission": "告诉老师孩子明天因发烧缺席",
        "mission_detail": "说明孩子的姓名、缺席原因和预计返校时间。",
        "counterpart": "班主任老师",
        "purpose": "请假联系",
        "channel": "电话",
        "required_information": ["孩子姓名", "缺席原因", "预计返校时间"],
        "max_turns": 3,
        "turn_plan": TURN_PLAN,
        "teacher_question": TURN_PLAN[0]["teacher_question_ko"],
    })


def _card():
    return {
        "sentences": [TURN_CONTENT[index]["target"] for index in (1, 2, 3)],
        "expected_question": TURN_PLAN[2]["teacher_question_ko"],
        "learned": "가지 못합니다 · 열이 나요 · 연락드리겠습니다",
    }


def attempt_fixture(turn: int, attempt: str):
    item = TURN_CONTENT[turn]
    question = TURN_PLAN[turn - 1]["teacher_question_ko"]
    if attempt == "first":
        return deepcopy({
            "analysis_mode": "fixture",
            "phase": "feedback",
            "turn": turn,
            "teacher_question": question,
            "transcript": item["spoken"],
            "target_sentence": item["target"],
            "feedback": {
                "language": {
                    "priority": item["priority"],
                    "said": item["spoken"],
                    "target": item["target"],
                    "explanation": item["explanation"],
                },
                "pronunciation": {
                    "score": item["first_score"],
                    "status": "전달 가능해요. 한 번 더 연습할 수 있어요" if item["first_score"] < 70 else "또렷하게 전달됐어요",
                    "focus_word": item["focus"],
                    "guide": item["guide"],
                },
            },
        })

    return deepcopy({
        "analysis_mode": "fixture",
        "phase": "turn_review",
        "turn": turn,
        "teacher_question": question,
        "transcript": item["target"],
        "target_sentence": item["target"],
        "comparison": {"before": item["first_score"], "after": item["retry_score"]},
        "feedback": {
            "language": {
                "priority": "意思传达清楚了",
                "said": item["target"],
                "target": item["target"],
                "explanation": "这句话已经可以直接用于实际通话。",
            },
            "pronunciation": {
                "score": item["retry_score"],
                "status": "매우 또렷하게 전달됐어요" if item["retry_score"] >= 85 else "또렷하게 전달됐어요",
                "focus_word": item["focus"],
                "guide": "这次更清楚。保持相同的速度。",
            },
        },
        "tomorrow_card": _card(),
    })
