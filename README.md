# 모두의 한국어

퇴근 후 10분, 이주민이 내일 반드시 해야 할 한국어 대화를 자기 목소리로 리허설하는 해커톤 MVP다.

## 실행

Python 3.9 이상과 Chrome이 필요하다.

```bash
chmod +x run.sh scripts/smoke.sh
./run.sh
```

Chrome에서 <http://127.0.0.1:8000>을 열고 microphone 권한을 허용한다.

## 현재 작동 범위

- 중국어 상황과 한국어 답변을 browser `MediaRecorder`로 실제 녹음
- 녹음한 audio를 FastAPI endpoint에 실제 전송
- 상황 → 학원 선생님 질문 → 어휘·문법/발음 feedback → 같은 문장 retry → 내일 카드의 전체 화면 흐름
- 장면 생성 시 세 turn의 목적을 고정하고 `对话 1/3`부터 `对话 3/3`까지 진행
- 첫 녹음을 browser에서 다시 듣기
- 첫 발화와 retry의 실제 pitch contour를 browser에서 추출해 겹쳐 보기
- 빈 audio와 잘못된 content type 거부

## AI 실행과 fixture 폴백

`.env`에 아래 값을 넣으면 첫 1회전은 실제 OpenAI 호출로 동작한다. 상황 녹음은 중국어 STT와
장면 생성으로, 첫 한국어 답변은 한국어 STT와 구조화된 언어 코칭으로 처리한다. 재시도 점수는
LLM이 아닌 목표 문장과 새 STT 결과의 결정적 편집거리 비교로 계산한다.

```bash
OPENAI_API_KEY=...
OPENAI_STT_MODEL=gpt-4o-transcribe
OPENAI_COACH_MODEL=gpt-5.6-luna
```

키가 없거나 STT·코칭 호출이 실패하면 같은 frontend JSON의 fixture를 반환한다. 이때 `GET /api/health`는
`analysis_mode: fixture`를, 키가 설정된 경우에는 `analysis_mode: live`를 반환한다. fixture 모드의
3-turn 데모 흐름은 그대로 보존한다.

## Backend 연결 지점

Browser가 사용하는 integration route는 AI 논리 작업과 분리돼 있다.

```text
GET  /api/health
POST /api/context                              raw audio -> scene + 3-turn plan
POST /api/attempts?attempt=first&turn=1        raw audio -> first feedback
POST /api/attempts?attempt=retry&turn=1        raw audio -> retry feedback
```

`turn`은 `1`, `2`, `3`만 허용한다. 라이브 모드는 60초 데모 범위인 첫 turn만 실제로 분석하고,
나머지 turn은 fixture 흐름으로 유지한다. Browser는 retry 때 같은 목표 문장과 첫 점수를 함께 보내므로
서버가 세션 상태를 저장하지 않고 새 전사 결과를 비교할 수 있다.

Pitch graph는 YIN으로 75–500Hz voiced frame을 추출하고 각 녹음의 중앙 pitch 기준 semitone으로
정규화한다. 정확도·정답 판정에는 사용하지 않으며, 유효 frame이 부족하면 graph 대신 재녹음을 안내한다.

## 검증

```bash
.venv/bin/python -m pytest -q
node --test tests/state.test.mjs
bash scripts/smoke.sh
```

`scripts/smoke.sh`는 정상 경로만 확인하지 않는다. 빈 `audio/webm` 요청이 실제로 HTTP 422를
반환하는 양성 대조도 함께 검사한다.
