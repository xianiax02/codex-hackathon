from copy import deepcopy


TURN_PLAN = [
    {"turn": 1, "objective_zh": "确认暂停上课的开始时间和时长", "teacher_question_ko": "언제부터 얼마나 쉬실 예정인가요?"},
    {"turn": 2, "objective_zh": "确认不是退课，而是暂时停课", "teacher_question_ko": "학원을 그만두는 건가요, 잠시 쉬는 건가요?"},
    {"turn": 3, "objective_zh": "询问重新上课前的联系时间", "teacher_question_ko": "다시 시작하는 것에 대해 궁금한 점이 있으세요?"},
]

TURN_CONTENT = {
    1: {
        "spoken": "다음 달부터 아이 학원 두 달 쉬고 싶어요.",
        "target": "다음 달부터 두 달 동안 아이 학원을 쉬고 싶어요.",
        "priority": "把时间说清楚",
        "explanation": "加上‘동안’，能清楚表达暂停上课的时间长度。",
        "focus": "두 달 동안",
        "guide": "把‘두 달 동안’连起来慢慢说。",
        "first_score": 68,
        "retry_score": 76,
    },
    2: {
        "spoken": "그만 아니고 두 달 후 다시 다녀요.",
        "target": "그만두는 건 아니고, 두 달 후에 다시 다니고 싶어요.",
        "priority": "意思更准确",
        "explanation": "用‘그만두는 건 아니고’说明只是暂时停课，不是退课。",
        "focus": "그만두는 건 아니고",
        "guide": "把长句分成两段，再自然地连接。",
        "first_score": 73,
        "retry_score": 82,
    },
    3: {
        "spoken": "다시 다니면 언제 연락해요?",
        "target": "다시 다니려면 언제 연락해야 하나요?",
        "priority": "问题更自然",
        "explanation": "用‘다니려면’能清楚表达重新上课的条件。",
        "focus": "다니려면",
        "guide": "把‘다니려면’连续读出来。",
        "first_score": 80,
        "retry_score": 87,
    },
}


def context_fixture():
    return deepcopy({
        "analysis_mode": "fixture",
        "source_transcript": "我想让孩子从下个月开始停两个月的课。以后想回来上课，应该什么时候联系呢？",
        "mission": "和补习班商量暂停两个月后再上课",
        "mission_detail": "说明开始时间、暂停时长，并询问重新上课前何时联系。",
        "counterpart": "补习班老师",
        "purpose": "暂停上课与重新报名咨询",
        "channel": "电话",
        "required_information": ["下个月开始", "暂停两个月", "重新上课前的联系时间"],
        "max_turns": 3,
        "turn_plan": TURN_PLAN,
        "teacher_question": TURN_PLAN[0]["teacher_question_ko"],
    })


def _card():
    return {
        "sentences": [TURN_CONTENT[index]["target"] for index in (1, 2, 3)],
        "expected_question": TURN_PLAN[2]["teacher_question_ko"],
        "learned": "두 달 동안 · 그만두는 건 아니고 · 다니려면",
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
