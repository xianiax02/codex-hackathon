# 내일의 한국어 AI API 계약 v1

## 목적과 경계

이 계약은 브라우저/백엔드와 AI 판단을 분리한다. 음성 녹음·STT 호출·점수 계산은 통합
레이어의 책임이고, AI는 이미 전사된 문장을 바탕으로 장면과 언어 코칭만 만든다. 따라서
LLM이 발음 점수나 실제로 듣지 못한 음소 오류를 만들면 안 된다.

`scene`, `feedback`, `retry`, `complete`는 AI 통합 레이어의 **논리 작업 이름**이다. 현재
브라우저 API인 `/api/context`와 `/api/attempts`는 raw audio를 받고 STT를 수행한 뒤 이
작업으로 변환한다. 따라서 프론트는 기존 라우트를 유지하고, 통합 레이어만 이 문서의
STT 완료 JSON과 UI 응답 JSON을 연결한다. 데모 중 키가 없으면
`ai/demo-fixtures.json`의 같은 응답을 그대로 반환해도 UI 계약은 바뀌지 않는다.

## 공통 규칙

- 모든 문자열은 UTF-8 JSON이고, 언어 태그는 `zh-CN` 또는 `ko-KR`이다.
- 사용자 음성 전사가 없으면 AI를 호출하거나 점수를 추측하지 않는다. `code`와 간체 중국어
  안내를 반환한다.
- `turn_id`는 같은 대화·같은 목표 문장을 묶는다. 재시도는 반드시 같은 `turn_id`를 쓴다.
- `next_action`은 화면 행동과 일대일이다. UI가 점수 때문에 다음 턴을 막으면 안 된다.

## 1. 장면 생성

### 요청: `POST /api/ai/scene`

```json
{
  "language": "zh-CN",
  "situation_transcript": "孩子生病了，明天不能去学校。我要给老师打电话。",
  "scenario_key": "school_absence"
}
```

`situation_transcript`는 중국어 STT의 원문이며 번역문으로 대체하지 않는다.

### 응답: 확인이 필요한 경우

```json
{
  "kind": "scene_confirmation",
  "confirmation_question_zh": "您是想说明孩子明天全天缺席，还是需要提前离校？",
  "known_context": {
    "partner_zh": "孩子的班主任",
    "purpose_zh": "说明孩子生病，联系学校",
    "channel_zh": "电话"
  },
  "next_action": "answer_confirmation"
}
```

### 응답: 장면 확정

```json
{
  "kind": "scene_ready",
  "scene": {
    "turn_id": "school-absence-1",
    "partner_ko": "담임 선생님",
    "partner_zh": "班主任老师",
    "purpose_zh": "说明孩子明天因病缺席",
    "channel_zh": "电话",
    "must_convey_zh": ["孩子明天缺席", "因为生病", "家长身份"],
    "partner_question_ko": "네, 어머님. 내일 결석하는 건가요?"
  },
  "next_action": "record_korean_reply"
}
```

## 2. 첫 한국어 답변의 언어 교정

### 요청: `POST /api/ai/feedback`

```json
{
  "turn_id": "school-absence-1",
  "partner_question_ko": "네, 어머님. 내일 결석하는 건가요?",
  "user_transcript_ko": "선생님, 아이가 아파서 내일 학교 못 갑니다.",
  "intended_context_zh": "孩子生病，明天全天缺席",
  "pronunciation_evidence": {
    "recognized_text_ko": "선생님 아이가 아파서 내일 학교 못 갑니다",
    "signal": { "status": "sufficient", "speech_ratio": 0.71, "clipping_ratio": 0.00 },
    "changed_or_missing_words_ko": ["못 갑니다"]
  }
}
```

### 응답

```json
{
  "kind": "language_feedback",
  "spoken_ko": "선생님, 아이가 아파서 내일 학교 못 갑니다.",
  "corrections": [
    {
      "priority": "politeness",
      "label_ko": "더 공손하게 말해요",
      "spoken_fragment_ko": "학교 못 갑니다",
      "suggestion_ko": "학교에 가지 못합니다",
      "explanation_zh": "对老师说明缺席时，用“가지 못합니다”会更礼貌、自然。"
    }
  ],
  "target_sentence_ko": "선생님, 아이가 아파서 내일 학교에 가지 못합니다.",
  "pronunciation": {
    "kind": "pronunciation_result",
    "score": 68,
    "status_ko": "전달 가능해요. 한 번 더 연습할 수 있어요",
    "status_zh": "对方大致能听懂。用下面的完整句子再练一次吧。",
    "evidence": "asr_and_signal",
    "focus_words_ko": ["못 갑니다"],
    "practice_hint_zh": "慢一点把“못 갑니다”连起来说。",
    "previous_score": null
  },
  "next_action": "retry_target_sentence"
}
```

`priority`는 `meaning`, `clarity`, `politeness`, `naturalness` 중 하나다. 배열은 이
순서로 정렬한다. 실제 발화에 없는 정보를 오류로 만들지 않으며, 오류가 없으면 빈 배열을
허용한다.

## 3. 발음 전달도와 재시도

### 통합 레이어가 산출하는 근거

```json
{
  "target_sentence_ko": "선생님, 아이가 아파서 내일 학교에 가지 못합니다.",
  "recognized_text_ko": "선생님 아이가 아파서 내일 학교에 가지 못합니다",
  "transcript_match_score": 94,
  "signal": {
    "status": "sufficient",
    "speech_ratio": 0.71,
    "clipping_ratio": 0.00
  },
  "changed_or_missing_words_ko": []
}
```

`transcript_match_score`는 공백·문장부호를 정규화한 뒤 목표 문장과 STT 결과의 음절
편집 거리를 0–100으로 환산한다. `signal.status`는 녹음 구간에 음성이 충분히 있고
클리핑이 심하지 않을 때만 `sufficient`이다. 이 값들은 LLM 입력·출력이 아니다.

점수 산식은 통합 레이어의 교체 가능한 내부 정책이다. 현재는 STT 목표문장 일치도와 녹음
신호 품질을 근거로 하지만, `score`의 산출 방식·가중치·세부 음성 특징은 API 계약에 넣지
않는다. 신호가 불충분하면 점수 대신 `unavailable`을 반환한다. 이는 실제 음성에서 나온
근거를 사용하는 **문장 전달도**이며, 음소·억양의 정확도 또는 사용자의 한국어 실력 등급이
아니다.

### 요청: retry 논리 작업

```json
{
  "turn_id": "school-absence-1",
  "target_sentence_ko": "선생님, 아이가 아파서 내일 학교에 가지 못합니다.",
  "recognized_text_ko": "선생님 아이가 아파서 내일 학교에 가지 못합니다",
  "previous_score": 68,
  "signal": {
    "status": "sufficient",
    "speech_ratio": 0.71,
    "clipping_ratio": 0.00
  },
  "changed_or_missing_words_ko": []
}
```

### 응답: retry 논리 작업

```json
{
  "kind": "pronunciation_result",
  "turn_id": "school-absence-1",
  "score": 95,
  "status_ko": "매우 또렷하게 전달됐어요",
  "status_zh": "这句话表达得很清楚。",
  "evidence": "asr_and_signal",
  "focus_words_ko": [],
  "practice_hint_zh": "保持刚才的速度即可。",
  "previous_score": 68,
  "next_action": "next_question"
}
```

점수 상태는 `85–100`, `70–84`, `50–69`, `0–49`의 잠긴 네 구간을 각각 `매우 또렷하게
전달됐어요`, `또렷하게 전달됐어요`, `전달 가능해요. 한 번 더 연습할 수 있어요`, `천천히
한 번 더 말해볼까요?`로 표시한다. `focus_words_ko`는 `changed_or_missing_words_ko`에서만
고르며, 신호가 불충분하면 빈 배열과 `evidence: "insufficient_audio"`를 반환한다.

## 4. 마무리 카드

사용자가 `다음으로`를 선택하면 통합 레이어는 `complete` 논리 작업으로 마지막 장면과
방금 확정한 문장을 전달한다. UI는 아래 응답의 `tomorrow_card`를 그대로 렌더링한다.

```json
{
  "kind": "practice_complete",
  "tomorrow_card": {
    "sentence_ko": "선생님, 아이가 아파서 내일 학교에 가지 못합니다.",
    "anticipated_question_ko": "결석계를 제출해 주실 수 있을까요?",
    "learned_points_zh": [
      "对老师说话时，用“가지 못합니다”会更礼貌。",
      "“못합니다”要连起来慢慢说。"
    ]
  },
  "next_action": "complete"
}
```

## 실패 응답

```json
{
  "kind": "input_error",
  "code": "KOREAN_TRANSCRIPT_UNAVAILABLE",
  "message_zh": "没有听清楚，请在安静的地方再说一次。",
  "next_action": "record_korean_reply"
}
```

허용 `code`는 `CHINESE_TRANSCRIPT_UNAVAILABLE`, `KOREAN_TRANSCRIPT_UNAVAILABLE`,
`AUDIO_SIGNAL_INSUFFICIENT`, `AI_RESPONSE_UNAVAILABLE`이다. 마지막 경우에는 마지막
성공 장면을 보존하고 재시도를 안내한다.

## 구현 선택

- STT: OpenAI `gpt-4o-transcribe`를 중국어·한국어 별도 파일 전사에 쓴다. 화자 분리가
  필요 없는 짧은 단일 발화이므로 diarization 모델은 쓰지 않는다.
- 코칭: OpenAI Responses API의 Structured Outputs로 `gpt-5.6-luna`에 장면·언어 교정
  JSON만 요청한다. 이 짧은 단일 장면에서는 Luna의 비용·속도가 적합하며, 모델명은 서버
  환경 변수 `OPENAI_COACH_MODEL`로 바꿀 수 있게 둔다. 고정 fixture와의 평가에서 언어
  품질이 부족할 때만 `gpt-5.6-terra`로 올린다.
- 채점: 브라우저 Worker 또는 백엔드의 결정적 함수가 맡는다. LLM이 score, focus word,
  음성 근거를 생성하게 하지 않는다.

OpenAI Structured Outputs는 제공한 JSON Schema 준수를 보장하지만 거절·토큰 한도 같은
실패는 별도로 처리해야 한다. 그래서 통합 레이어는 응답 `kind`와 필수 키를 검사한 후
`AI_RESPONSE_UNAVAILABLE`로 전환한다.
