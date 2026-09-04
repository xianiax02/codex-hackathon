# Hackathon Presentation Implementation Plan

> **For agentic workers:** Implement this plan one task at a time, in order. Steps use checkbox (`- [ ]`) syntax — check a step off only after its verification step actually passed, and stop at each review checkpoint rather than running ahead.

**Goal:** 실제 이주민 학부모 사례에서 시작해 60초 live demo로 이어지는 3분 30초 HTML 발표자료와 발표 대본을 만든다.

**Architecture:** `presentation/index.html`은 여섯 slide의 semantic content를 소유하고, `presentation/style.css`은 16:9 stage와 제품 visual system을 담당한다. `presentation/deck.js`는 keyboard navigation, timer, progress, demo URL만 관리한다. Node built-in test가 slide 수, timing, 실제 사례, fixture disclosure를 검사한다.

**Tech Stack:** HTML5, CSS, browser JavaScript ES module, Node built-in test runner

## Global Constraints

- 총 발표 시간은 3분 30초이며 live demo는 60초다.
- 순서는 `필요성 → 사회문제 → 서비스 소개 → user flow와 demo → LLM → Codex 검증 → 결론`이다.
- 실제 사례는 `주변 이주민 학부모`로 익명화하고 확인하지 않은 개인정보를 추가하지 않는다.
- 단일 사례를 전체 이주민의 경험으로 일반화하지 않는다.
- 현재 실제 동작과 fixture 범위를 분리해 표시한다.
- 제품의 `#6046E8`, 흰색, 연한 보라색 visual system을 유지한다.
- 기존 `web/`, `app/`, `ai/`, `tests/pitch.test.mjs`는 수정하지 않는다.

---

### Task 1: Presentation content contract

**Files:**
- Create: `tests/presentation.test.mjs`
- Create: `presentation/index.html`

**Interfaces:**
- Consumes: approved six-slide narrative and current fixture boundary from `README.md`
- Produces: six `<section class="slide">` elements with `data-seconds` totaling `150`; live demo occupies the remaining `60` seconds

- [ ] **Step 1: Write the failing content test**

```javascript
const html = await readFile(new URL("../presentation/index.html", import.meta.url), "utf8");
assert.equal((html.match(/class="slide/g) || []).length, 6);
assert.match(html, /주변 이주민 학부모/);
assert.match(html, /두 달/);
assert.match(html, /analysis.*fixture|fixture.*분석/is);
assert.equal([...html.matchAll(/data-seconds="(\d+)"/g)].reduce((sum, m) => sum + Number(m[1]), 0), 150);
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/presentation.test.mjs`

Expected: FAIL because `presentation/index.html` does not exist.

- [ ] **Step 3: Write the six semantic slides**

Create a complete HTML document with these titles and timing values:

```html
<section class="slide is-active" data-seconds="30"><h1>전화 한 통을 앞둔 학부모</h1></section>
<section class="slide" data-seconds="35"><h2>생활의 결정은 실시간 한국어로 이루어집니다</h2></section>
<section class="slide" data-seconds="15"><h2>내일의 대화를 오늘 먼저 연습합니다</h2></section>
<section class="slide" data-seconds="25"><h2>LLM이 맡는 세 가지 판단</h2></section>
<section class="slide" data-seconds="25"><h2>작동 범위와 검증</h2></section>
<section class="slide" data-seconds="20"><h2>내일 꼭 해야 할 한마디</h2></section>
```

Add a `demo-link` anchor on slide 3 whose default `href` is `/` and whose copy says `60초 live demo 열기`. Add notes in `<aside class="speaker-notes">` for every slide.

- [ ] **Step 4: Run content test to verify it passes**

Run: `node --test tests/presentation.test.mjs`

Expected: all presentation content assertions pass.

### Task 2: Visual system and navigation

**Files:**
- Create: `presentation/style.css`
- Create: `presentation/deck.js`
- Modify: `presentation/index.html`
- Modify: `tests/presentation.test.mjs`

**Interfaces:**
- Consumes: `.slide`, `[data-seconds]`, `#demo-link`, `#progress`, `#timer`
- Produces: `showSlide(index)`, `startTimer()`, `resetTimer()`, query parameter `?demo=<URL>`

- [ ] **Step 1: Extend the test for navigation hooks**

```javascript
assert.match(html, /id="progress"/);
assert.match(html, /id="timer"/);
const js = await readFile(new URL("../presentation/deck.js", import.meta.url), "utf8");
assert.match(js, /ArrowRight/);
assert.match(js, /ArrowLeft/);
assert.match(js, /URLSearchParams/);
```

- [ ] **Step 2: Run test to verify the new assertions fail**

Run: `node --test tests/presentation.test.mjs`

Expected: FAIL because navigation assets do not exist.

- [ ] **Step 3: Implement keyboard and timer behavior**

`deck.js` must clamp the slide index, update `aria-hidden`, update progress text, support `ArrowRight`, `Space`, `ArrowLeft`, `Home`, `End`, and map `?demo=` to the demo anchor. `T` starts or pauses the stopwatch and `R` resets it.

- [ ] **Step 4: Implement the 16:9 product-matched layout**

Use `aspect-ratio: 16 / 9`, `#6046E8`, `#18212F`, `#F0EDFF`, and Noto/system sans-serif. Keep titles at least `48px`, body at least `22px`, and add a print stylesheet that places one slide per landscape page.

- [ ] **Step 5: Run content and hook tests**

Run: `node --test tests/presentation.test.mjs`

Expected: all assertions pass.

### Task 3: Speaker script and factual verification

**Files:**
- Create: `presentation/speaker-script.md`
- Modify: `CODEX_LOG.md`

**Interfaces:**
- Consumes: slide timing and verified claims in `docs/product-brief.md`, `README.md`, `tests/test_api.py`, `tests/state.test.mjs`
- Produces: timestamped Korean script totaling 210 seconds and a traceable validation record

- [ ] **Step 1: Write the timestamped script**

The script must include exact blocks for `0:00–0:30`, `0:30–1:05`, `1:05–1:20`, `1:20–2:20`, `2:20–2:45`, `2:45–3:10`, and `3:10–3:30`. It must disclose that microphone capture, audio upload, state flow, and pitch contour run, while STT and feedback remain fixture.

- [ ] **Step 2: Run all current automated tests**

Run: `.venv/bin/python -m pytest -q && node --test tests/state.test.mjs tests/pitch.test.mjs tests/presentation.test.mjs`

Expected: API, state, pitch positive control, silence abstention, and presentation contract all pass.

- [ ] **Step 3: Run static wording checks**

Run: `rg -n 'T[B]D|T[O]DO|실제 AI 분석|모든 이주민|원어민처럼' presentation`

Expected: no unsupported or placeholder wording.

- [ ] **Step 4: Record the work in CODEX_LOG**

Append one row that names the six-slide HTML deck, 210-second timing contract, automated checks, and human-selected real case.

### Task 4: Browser render review and wiki handoff

**Files:**
- Modify: `presentation/index.html` only if browser review finds copy or overflow defects
- Modify: `presentation/style.css` only if browser review finds layout defects
- Copy: `presentation/` to `/Users/xian/personal-wiki/research/커리어/Codex 해커톤 (2026-09-04)/05_구현 문서/presentation/`

**Interfaces:**
- Consumes: local static files or FastAPI-served presentation route
- Produces: visually reviewed 1280×720 deck and checksum-identical wiki copy

- [ ] **Step 1: Serve and open the deck**

Run: `python3 -m http.server 8765 --directory presentation`

Expected: `GET /` returns 200 and renders slide 1.

- [ ] **Step 2: Inspect every slide at 1280×720**

Verify readable titles, no clipping, correct progress, demo link, and coherent visual rhythm. Repair source CSS or HTML and repeat the check if any defect appears.

- [ ] **Step 3: Verify keyboard and demo link**

Exercise forward, backward, Home, End, timer, and `?demo=http://127.0.0.1:8000` behavior in the browser.

- [ ] **Step 4: Copy the final presentation to the wiki and compare checksums**

Copy the four files in `presentation/` while preserving filenames. Compare SHA-256 values between repo and wiki copies; expected result is no diff.
