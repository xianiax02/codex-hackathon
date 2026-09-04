# Rehearsal Shell Implementation Plan

> **For agentic workers:** Implement this plan one task at a time, in order. Steps use checkbox (`- [ ]`) syntax — check a step off only after its verification step actually passed, and stop at each review checkpoint rather than running ahead.

**Goal:** 중국어 상황 음성 입력부터 한국어 답변, 두 축 교정, 같은 문장 재시도, 마무리까지 승인된 데모를 브라우저에서 끝까지 실행한다.

**Architecture:** FastAPI가 정적 web app과 demo fixture API를 제공한다. Browser `MediaRecorder`가 실제 microphone audio를 서버로 보내고, 현재는 유현님의 AI 계약과 같은 자리에 고정 fixture를 반환한다. UI state machine은 API 응답만 렌더링하므로 이후 `ai/` 구현을 바꾸지 않고 연결할 수 있다.

**Tech Stack:** Python 3.9, FastAPI, Uvicorn, HTML, CSS, browser MediaRecorder, Node built-in test runner, pytest

## Global Constraints

- `ai/`, `docs/ai-correction-spec.md`, `docs/ai-api-contract.md`, `AGENTS.md`, `docs/product-brief.md`, `docs/brainstorm.md`, `DESIGN.md`를 수정하지 않는다.
- 데스크톱 1280px, 1:2 layout, `zh-CN` 맥락과 한국어 역할극을 유지한다.
- 발음 전달도는 문장 단위이며 한국어 능력 등급이나 합격 판정으로 표현하지 않는다.
- 음성 분석 근거가 없으면 오류를 새로 만들지 않고 재녹음을 안내한다.
- 실제 AI 연결 전 범위는 fixture임을 README와 화면 상태에 명시한다.

---

### Task 1: Demo contract와 server shell

**Files:**
- Create: `requirements.txt`
- Create: `app/__init__.py`
- Create: `app/main.py`
- Create: `app/demo_fixture.py`
- Create: `tests/test_api.py`

**Interfaces:**
- Consumes: raw `audio/*` request body와 `attempt=first|retry`
- Produces: `GET /api/health`, `POST /api/context`, `POST /api/attempts?attempt=first|retry`

- [ ] **Step 1: 실패하는 API test 작성**

```python
def test_empty_audio_is_rejected(client):
    response = client.post("/api/context", content=b"", headers={"content-type": "audio/webm"})
    assert response.status_code == 422

def test_first_attempt_returns_two_feedback_axes(client):
    response = client.post("/api/attempts?attempt=first", content=b"audio", headers={"content-type": "audio/webm"})
    assert set(response.json()["feedback"]) == {"language", "pronunciation"}
```

- [ ] **Step 2: test 실패 확인**

Run: `pytest -q`
Expected: FAIL because `app.main` does not exist.

- [ ] **Step 3: fixture와 endpoint 최소 구현**

```python
@app.post("/api/attempts")
async def analyze_attempt(request: Request, attempt: Literal["first", "retry"]):
    audio = await require_audio(request)
    return JSONResponse(first_attempt() if attempt == "first" else retry_attempt())
```

- [ ] **Step 4: API test 통과 확인**

Run: `pytest -q tests/test_api.py`
Expected: all tests pass.

### Task 2: UI state machine과 contract test

**Files:**
- Create: `web/state.mjs`
- Create: `tests/state.test.mjs`

**Interfaces:**
- Consumes: `idle|context|question|feedback|retry|complete` state와 event
- Produces: `transition(state, event)` 및 잘못된 전이를 거부하는 `Error`

- [ ] **Step 1: 정상 흐름과 잘못된 전이 test 작성**

```javascript
assert.equal(transition("idle", "CONTEXT_READY"), "question");
assert.equal(transition("question", "FIRST_ANALYZED"), "feedback");
assert.throws(() => transition("idle", "RETRY_ANALYZED"));
```

- [ ] **Step 2: test 실패 확인**

Run: `node --test tests/state.test.mjs`
Expected: FAIL because `web/state.mjs` does not exist.

- [ ] **Step 3: 허용된 전이 table 구현**

```javascript
const transitions = {
  idle: { CONTEXT_READY: "question" },
  question: { FIRST_ANALYZED: "feedback" },
  feedback: { RETRY_STARTED: "retry", NEXT: "complete" },
  retry: { RETRY_ANALYZED: "complete" },
};
```

- [ ] **Step 4: state test 통과 확인**

Run: `node --test tests/state.test.mjs`
Expected: all tests pass.

### Task 3: 승인된 1:2 rehearsal UI와 microphone 흐름

**Files:**
- Create: `web/index.html`
- Create: `web/style.css`
- Create: `web/app.js`

**Interfaces:**
- Consumes: Task 1 JSON API, Task 2 `transition`, browser `MediaRecorder`
- Produces: 중국어 상황 녹음, 한국어 첫 답변, 두 축 feedback, retry, 완료 card

- [ ] **Step 1: semantic DOM과 여섯 상태 section 작성**

```html
<main class="rehearsal-shell">
  <aside aria-label="明天的任务"></aside>
  <section aria-live="polite" aria-labelledby="call-title"></section>
</main>
```

- [ ] **Step 2: `DESIGN.md` token과 1:2 layout 구현**

```css
.rehearsal-shell { display: grid; grid-template-columns: 1fr 2fr; gap: 16px; }
button:focus-visible { outline: 3px solid #6046e8; outline-offset: 3px; }
```

- [ ] **Step 3: microphone recorder와 raw audio upload 구현**

```javascript
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
const recorder = new MediaRecorder(stream);
recorder.addEventListener("stop", () => uploadAudio(new Blob(chunks, { type: recorder.mimeType })));
```

- [ ] **Step 4: first/retry 응답을 두 feedback panel과 before/after 점수로 렌더링**

```javascript
score.textContent = `${result.pronunciation.score}점`;
status.textContent = result.pronunciation.status;
```

- [ ] **Step 5: 정적 asset과 browser route 확인**

Run: `uvicorn app.main:app --port 8000` then `curl -I http://127.0.0.1:8000/`
Expected: `HTTP/1.1 200 OK`.

### Task 4: 실행 문서, 범위 공개, end-to-end 검증

**Files:**
- Create: `README.md`
- Modify: `CODEX_LOG.md`
- Create: `scripts/smoke.sh`

**Interfaces:**
- Consumes: 완성된 server와 browser app
- Produces: 한 명령 실행법, fixture/실제 구현 경계, 재현 가능한 smoke test

- [ ] **Step 1: README에 실행법과 정직한 범위 작성**

```text
현재 실제 동작: microphone capture, audio upload, 화면 state, retry 비교
현재 fixture: STT, 어휘·문법 교정, 발음 전달도 산출
```

- [ ] **Step 2: 빈 audio가 실패하는 양성 대조와 정상 audio smoke 작성**

```bash
curl --fail http://127.0.0.1:8000/api/health
test "$(curl -s -o /dev/null -w '%{http_code}' -X POST http://127.0.0.1:8000/api/context)" = 422
```

- [ ] **Step 3: 전체 자동 검증 실행**

Run: `pytest -q && node --test tests/state.test.mjs && bash scripts/smoke.sh`
Expected: Python tests, state tests, valid API path pass; empty-audio positive control returns 422.

- [ ] **Step 4: `CODEX_LOG.md`에 구현·검증·사람이 고정한 spec 기록**

```text
준현님 소유 범위만 구현 | 실제 microphone upload와 fixture end-to-end | empty audio 422 양성 대조 | 기존 spec 그대로 유지
```

### Task 5: 3-turn 역할극 loop

**Files:**
- Modify: `app/demo_fixture.py`
- Modify: `app/main.py`
- Modify: `web/state.mjs`
- Modify: `web/app.js`
- Modify: `web/index.html`
- Test: `tests/test_api.py`
- Test: `tests/state.test.mjs`

**Interfaces:**
- Consumes: `max_turns: 3`, `turn_plan`, 현재 `turn=1|2|3`
- Produces: turn당 first/retry feedback와 `对话 N/3` 진행 표시

- [ ] **Step 1: 세 turn fixture와 loop state test 작성 후 실패 확인**

Run: `.venv/bin/python -m pytest -q && node --test tests/state.test.mjs`
Expected: 새로운 `turn_plan`과 `NEXT_QUESTION` assertion이 실패한다.

- [ ] **Step 2: context fixture에 세 목적을 만들고 turn parameter로 응답 선택**

```python
@app.post("/api/attempts")
async def analyze_attempt(request: Request, attempt: Literal["first", "retry"], turn: int = Query(1, ge=1, le=3)):
    await require_audio(request)
    return JSONResponse(attempt_fixture(turn, attempt))
```

- [ ] **Step 3: retry 뒤 완료하지 않고 다음 질문으로 돌아가는 state 구현**

```javascript
feedback: { RETRY_STARTED: "retry", NEXT_QUESTION: "question", COMPLETE: "complete" },
retry: { RETRY_ANALYZED: "feedback" },
```

- [ ] **Step 4: 세 번째 turn에서만 내일 카드로 종료되는지 확인**

Run: `.venv/bin/python -m pytest -q && node --test tests/state.test.mjs`
Expected: all tests pass.

### Task 6: 실제 first/retry pitch contour 비교

**Files:**
- Create: `web/pitch.mjs`
- Create: `tests/pitch.test.mjs`
- Modify: `web/app.js`
- Modify: `web/index.html`
- Modify: `web/style.css`

**Interfaces:**
- Consumes: browser가 녹음한 `Blob`, 75–500Hz voiced frame
- Produces: `extractPitchContour(AudioBuffer)`, speaker-relative semitone SVG와 text summary

- [ ] **Step 1: 220Hz sine과 silence 양성 대조 test 작성 후 실패 확인**

```javascript
assert.ok(Math.abs(yinPitch(sineWave(220), 16000) - 220) < 3);
assert.equal(yinPitch(new Float32Array(2048), 16000), null);
```

- [ ] **Step 2: YIN과 speaker-relative semitone 정규화 구현**

```javascript
const semitone = 12 * Math.log2(point.hz / medianHz);
```

- [ ] **Step 3: 첫 발화와 재시도를 실제 audio에서 추출해 SVG에 overlay**

첫 발화는 보라색 실선, 재시도는 초록색 점선으로 그리고 유효 frame 수와 pitch 범위를 text로 제공한다.

- [ ] **Step 4: 자동 test와 Chrome render 재검증**

Run: `node --test tests/pitch.test.mjs tests/state.test.mjs && bash scripts/smoke.sh`
Expected: sine detection, silence abstention, state, server smoke가 모두 통과한다.
