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
- 상황 → 담임 질문 → 어휘·문법/발음 feedback → 같은 문장 retry → 내일 카드의 전체 화면 흐름
- 장면 생성 시 세 turn의 목적을 고정하고 `对话 1/3`부터 `对话 3/3`까지 진행
- 첫 녹음을 browser에서 다시 듣기
- 빈 audio와 잘못된 content type 거부

## 아직 fixture인 범위

- 중국어·한국어 speech-to-text
- 어휘·문법 교정 생성
- 발음 전달도 점수와 집중 단어 산출
- retry 점수 비교와 내일 카드 생성

화면 하단과 `GET /api/health`의 `analysis_mode`가 이 범위를 `fixture`로 명시한다. 유현님이 소유한
`ai/`와 `docs/ai-api-contract.md`가 준비되면 `app/main.py`의 세 endpoint 내부만 실제 AI 호출로
교체하고, frontend JSON 모양은 유지한다.

## Backend 연결 지점

Browser가 사용하는 integration route는 AI 논리 작업과 분리돼 있다.

```text
GET  /api/health
POST /api/context                              raw audio -> scene + 3-turn plan
POST /api/attempts?attempt=first&turn=1        raw audio -> first feedback
POST /api/attempts?attempt=retry&turn=1        raw audio -> retry feedback
```

`turn`은 `1`, `2`, `3`만 허용한다. Backend는 raw audio를 STT로 전사한 뒤
`docs/ai-api-contract.md`의 `scene`, `feedback`, `retry`, `complete` 논리 작업을 호출하고,
현재 fixture와 같은 frontend JSON으로 조합한다.

`DESIGN.md`의 first/retry pitch contour graph는 승인됐지만 이 draft에는 아직 구현되지 않았다.

## 검증

```bash
.venv/bin/python -m pytest -q
node --test tests/state.test.mjs
bash scripts/smoke.sh
```

`scripts/smoke.sh`는 정상 경로만 확인하지 않는다. 빈 `audio/webm` 요청이 실제로 HTTP 422를
반환하는 양성 대조도 함께 검사한다.
