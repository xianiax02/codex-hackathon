from app.scoring import first_attempt_score, retry_score


def test_first_attempt_score_uses_only_the_three_required_meanings():
    assert first_attempt_score("아이 아파서 학교 못 가요") == 75
    assert first_attempt_score("아이가 아파서 내일 학교에 못 갑니다") == 100


def test_retry_score_compares_only_normalized_hangul_syllables():
    assert retry_score("학교에 가지 못합니다.", "학교에 가지 못합니다") == 100
    assert retry_score("가", "나") == 0
