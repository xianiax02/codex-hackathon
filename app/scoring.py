import re


def _hangul_only(text: str) -> str:
    return "".join(re.findall(r"[가-힣]", text))


def first_attempt_score(transcript: str) -> int:
    normalized = _hangul_only(transcript)
    score = 0
    if "아이" in normalized and ("아프" in normalized or "아파" in normalized):
        score += 35
    if "내일" in normalized:
        score += 25
    if "학교" in normalized and any(
        marker in normalized for marker in ("못가", "못갑", "가지못", "결석")
    ):
        score += 40
    return score


def retry_score(target_sentence: str, transcript: str) -> int:
    target = _hangul_only(target_sentence)
    spoken = _hangul_only(transcript)
    if not target or not spoken:
        return 0

    previous_row = list(range(len(spoken) + 1))
    for target_index, target_character in enumerate(target, start=1):
        current_row = [target_index]
        for spoken_index, spoken_character in enumerate(spoken, start=1):
            substitution_cost = target_character != spoken_character
            current_row.append(
                min(
                    previous_row[spoken_index] + 1,
                    current_row[spoken_index - 1] + 1,
                    previous_row[spoken_index - 1] + substitution_cost,
                )
            )
        previous_row = current_row

    distance = previous_row[-1]
    return round(100 * (1 - distance / max(len(target), len(spoken))))


def pronunciation_status(score: int) -> str:
    if score >= 85:
        return "매우 또렷하게 전달됐어요"
    if score >= 70:
        return "또렷하게 전달됐어요"
    if score >= 50:
        return "전달 가능해요. 한 번 더 연습할 수 있어요"
    return "천천히 한 번 더 말해볼까요?"


def missing_target_words(target_sentence: str, transcript: str) -> list[str]:
    recognized = set(re.findall(r"[가-힣]+", transcript))
    missing: list[str] = []
    for word in re.findall(r"[가-힣]+", target_sentence):
        if word not in recognized and word not in missing:
            missing.append(word)
    return missing[:1]
