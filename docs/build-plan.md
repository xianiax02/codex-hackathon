# 모두의 한국어 — 해커톤 실행 계획

## 0. 이번 결과물의 한 문장

이주민 부모가 자녀의 학원 휴원과 재등록 연락 시점을 입력하고, AI 학원 선생님과 세 턴을 말해 본 뒤,
전달을 막은 표현과 소리 하나를 고쳐 다시 말하고, 바로 쓸 세 문장을 가져간다.

성공 기준은 한국어 실력 평가가 아니라 **자녀 교육 관련 결정을 자기 목소리로 전달할 준비가 되었는가**다.

## 1. 시작 전에 5분 안에 합의할 것

| 항목 | 추천 | 이유 |
|---|---|---|
| demo 사용자 | 익명 이주민 부모 | 실제 가족의 개인정보 없이 문제의 긴급성을 보인다 |
| 상황 입력 | 한국어 text | 입력 단계의 음성 인식 변수를 제거하고 역할극에 시간을 쓴다 |
| 역할극 입력 | microphone | 말하기 제품이라는 핵심을 화면에서 증명한다 |
| 발음 피드백 | 목표 문장과 음성 인식 결과의 차이 1개 | 근거 없는 accent 점수나 국적 일반화를 피한다 |
| stack | FastAPI + single-page HTML/CSS/JS | 유현의 Python 작업과 준현의 화면 작업을 파일 단위로 분리하기 쉽다 |
| demo 장면 | 다음 달부터 두 달간 학원을 쉬고 재등록 연락 시점을 묻기 | 가족·번역기 의존 없이 교육 결정을 직접 전달하는 문제를 보인다 |

API와 microphone 실측에 실패하면 발음 기능을 연기하지 않는다. `발음 분석` 대신 확인 가능한
`잘 전달되지 않은 단어` 피드백으로 명칭과 발표 문구를 함께 낮춘다.

## 2. 60초 demo contract

| 시간 | 사용자의 행동 | 화면의 반응 | 증명하는 것 |
|---:|---|---|---|
| 0–7초 | `다음 달부터 두 달 동안 아이 학원을 쉬고 싶어요. 다시 다니려면 언제 연락해야 하나요?` 입력 | 상대·목적·필수 정보와 세 턴 범위가 생성됨 | LLM이 생활 목표를 rehearsal로 바꾼다 |
| 7–15초 | `연습 시작` | 학원 선생님이 첫 질문을 함 | 고정 교재가 아닌 role-play다 |
| 15–39초 | 세 질문에 답하고 핵심 표현을 retry | 발화 transcript, 교정, pitch before/after가 나타남 | 실제 발화에 맞춰 우선순위를 고르고 적용한다 |
| 39–52초 | 다음 질문으로 진행 | 휴원 기간, 일시 휴원, 재연락 시점을 차례로 확인 | 대화가 한마디로 끝나지 않는다 |
| 52–60초 | 완료 | 실제 통화에 쓸 세 문장과 예상 질문 하나가 남음 | 학습이 실제 행동으로 끝난다 |

demo 중 AI 대화는 **질문·답변·retry 3턴**으로 제한한다. 범위 밖의 자유 대화는 만들지 않는다.

## 3. 구현 범위

### P0 — 없으면 demo가 성립하지 않음

- 상황 text 입력
- LLM이 `상대`, `목적`, `필수 정보`, `첫 질문`, `연습할 짧은 문장` 생성
- microphone 녹음과 audio 업로드
- 첫 발화 transcript 표시
- 쉬운 표현 1개 + 관찰 가능한 전달 문제 1개
- 같은 목표 문장 retry와 before/after 표시
- 내일 문장 3개 + 예상 질문 1개
- API 실패 시 관객 앞에서 복구할 수 있는 명시적 demo fixture

### P1 — P0가 끝까지 돈 뒤에만

- 학원 선생님 질문 음성 재생
- 녹음 중 waveform 또는 timer
- Vietnamese 등 주사용 언어로 짧은 도움말
- 결과 카드 copy 버튼

### 만들지 않음

- 로그인, 회원가입, DB, history, settings
- 학교·병원·직장 scenario 선택 화면
- 종합 점수, accent 등급, 국적 기반 진단
- 실시간 streaming 대화, 여러 turn, 사진 입력
- 반응형 완성도와 animation polish

## 4. 동작 원리와 경계

```text
situation text
    -> LLM: rehearsal JSON 생성
    -> UI: 선생님의 질문과 목표 문장 표시
microphone audio
    -> speech-to-text
    -> 목표 문장 / transcript 비교
    -> LLM: 전달에 중요한 표현 1개와 관찰된 차이 1개 선택
retry audio
    -> speech-to-text
    -> before / after 비교
    -> LLM: 내일 카드 JSON 생성
```

LLM은 자유 문장을 role-play 구조로 바꾸고, 사용자의 발화 맥락에서 무엇을 먼저 고칠지 선택한다.
문자열 비교만으로 특정 phoneme을 정확히 진단했다고 주장하지 않는다. ASR이 다르게 들은 단어만
`잘 전달되지 않은 단어`로 보여 주며, 발음 원인을 말하려면 별도 실측을 통과해야 한다.

모든 LLM 응답은 UI 문장이 아니라 고정 schema의 JSON으로 받는다. parse 실패 시 한 번 재시도하고,
그 뒤에는 demo fixture로 전환한다. session state는 browser 또는 process memory에만 둔다.

## 5. 파일 분리와 API contract

같은 파일을 동시에 수정하지 않는다.

| 소유자 | 파일 | 책임 |
|---|---|---|
| 준현 | `web/index.html`, `web/app.js`, `web/style.css` | 화면, microphone, state transition, demo 연출 |
| 유현 | `app/main.py`, `app/services/*.py`, `app/prompts/*.py` | FastAPI, STT, LLM schema, feedback |
| 한 명만 | `tests/`, `docs/api-contract.md` | contract fixture와 smoke test |

최소 endpoint는 세 개다.

```text
POST /api/scenarios       situation text -> rehearsal JSON
POST /api/attempts        audio + rehearsal -> transcript + feedback JSON
POST /api/retries         audio + rehearsal + first attempt -> comparison + card JSON
```

Frontend는 첫 30분 동안 backend 없이 같은 JSON fixture로 완주할 수 있어야 한다. Backend는 동일한
fixture를 contract test로 사용한다. API schema를 바꿀 때는 구현 파일보다 `api-contract.md`를 먼저
바꾼다.

## 6. 150분 timebox

| 시간 | 준현 | 유현 | 통합 gate |
|---:|---|---|---|
| T+0–10 | demo 문장·화면 state 확정 | audio/STT 최소 호출 실측 | stack과 API contract 합의 |
| T+10–30 | fixture 기반 전체 UI | scenario JSON endpoint | **fixture로 60초 흐름 완주** |
| T+30–55 | microphone 녹음·API 연결 | audio -> transcript endpoint | 녹음 하나가 화면에 transcript로 돌아옴 |
| T+55–75 | feedback·retry 화면 | feedback와 card schema | 첫 시도부터 card까지 실제 API로 완주 |
| T+75–90 | before/after 연출 | 발음 주장 가능 범위 검증 | 발음 gate 결정, 실패 시 문구 즉시 축소 |
| T+90–110 | 시각 hierarchy와 loading | error/timeout/parse fallback | 정상·실패 경로 각각 1회 완주 |
| T+110–125 | 발표 화면 고정 | API preflight와 fixture 고정 | demo용 입력·audio로 3회 연속 성공 |
| T+125–140 | 발표 대본·화면 녹화 | 기술 설명 20초 작성 | 3분 30초 안에 발표 1회 |
| T+140–150 | 치명적 bug만 수정 | 치명적 bug만 수정 | 마지막 clean run 후 코드 freeze |

T+30에 end-to-end가 안 돌면 기능을 추가하지 않고 fixture 완주부터 복구한다. T+90 이후에는 P1을
시작하지 않는다.

## 7. 검증 gate

### Gate A — speech 경로, T+30까지

1. 의도 문장이 알려진 demo audio 두 개를 준비한다.
2. 하나는 전달 가능한 발화, 하나는 의도적으로 핵심 단어가 다른 발화로 둔다.
3. 두 audio가 같은 결과를 내면 검사기가 차이를 못 잡는 것이므로 발음 주장을 제거한다.
4. 다른 microphone과 행사장 소음에서도 한 번 확인한다.

### Gate B — feedback 근거, T+75까지

- 입력 transcript에 없는 오류를 feedback이 지어내면 실패다.
- `국적 때문에 이 소리를 틀렸다`는 문장이 나오면 실패다.
- 고칠 것이 없을 때 억지 오류 대신 `목적이 잘 전달됐어요`가 나와야 한다.
- feedback은 항상 표현 1개와 전달 문제 최대 1개다.

### Gate C — demo reliability, T+125까지

- 새 browser session에서 실제 API 경로 3회 연속 완주
- network failure를 강제로 만들었을 때 fixture 전환 확인
- 실패 fixture를 넣어 JSON schema 검사가 실제로 실패하는지 양성 대조
- 발표 전체를 stopwatch로 재서 3분 30초 이내 확인

`테스트 통과` 대신 위 입력과 기대 결과를 기록한다.

## 8. 중단 순서

시간이 부족하면 아래 순서로 자른다.

1. waveform과 animation
2. AI 질문 음성 재생
3. 주사용 언어 도움말
4. 자유 발화에 대한 phoneme 원인 설명
5. 실제 API retry 비교

마지막까지 남기는 것은 `상황 -> 첫 발화 -> 두 가지 피드백 -> 다시 말하기 -> 내일 카드`다.

## 9. 발표 3분 30초 배분

| 구간 | 시간 | 내용 |
|---|---:|---|
| 문제 장면 | 0:00–0:35 | 이주민 학부모가 자녀 교육 결정을 직접 전달하지 못해 가족이나 번역기에 의존한다 |
| 기존 방식의 틈 | 0:35–0:55 | 번역은 문장을 주지만 실제 대화를 대신 연습시켜 주지 않는다 |
| 제품 한 문장 | 0:55–1:05 | 내일의 대화를 오늘 10분 먼저 살아본다 |
| live demo | 1:05–2:05 | 위 60초 contract 그대로 |
| 왜 LLM인가 | 2:05–2:35 | 상황 구조화, 반응형 role-play, 실제 발화에서 우선순위 선택 |
| 사회적 가치와 경계 | 2:35–3:05 | 목적 전달이 성공 기준이며 국적·accent를 점수화하지 않는다 |
| Codex 활용과 결론 | 3:05–3:30 | 규칙·contract·양성 대조로 빠르게 만들면서 과장을 막은 과정 |

발표의 마지막 문장은 다음으로 고정한다.

> 한국어 전체를 오늘 가르치려 하지 않습니다. 내일 꼭 해야 할 한마디를 오늘 자기 목소리로 끝냅니다.
