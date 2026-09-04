# 내일의 한국어 3분 30초 발표 자료 설계

## 목표

심사위원이 첫 30초 안에 문제 당사자와 불편한 순간을 이해하고, 60초 live demo에서 입력 하나와
결과 하나, 사용자의 재시도를 확인하게 한다. 발표는 구현된 범위와 fixture 범위를 구분하고,
Codex를 이용해 빠르게 만든 과정뿐 아니라 잘못된 성공 신호를 막은 검증도 보여 준다.

## 결과물

- 배포 가능한 single-page HTML slide deck
- 16:9, keyboard navigation, 발표자용 timing 표시
- live demo URL을 새 tab으로 여는 버튼
- slide별 speaker notes를 HTML 내부에 포함
- 총 6장, live demo 60초를 포함해 3분 30초

PPTX는 만들지 않는다. HTML은 현재 FastAPI app과 독립된 정적 파일로 두고, 배포 환경에서는 같은
origin의 `/` 또는 설정한 demo URL을 연다.

## 발표 구조

| 시간 | 화면 | 주장과 근거 |
| ---: | --- | --- |
| 0:00–0:20 | 1. 내일 해야 할 통화 | 이주민 부모가 아이 결석을 담임에게 직접 알려야 하는 장면 |
| 0:20–0:45 | 2. 교재보다 먼저 닥치는 대화 | 외국인 취업자 약 101만 명, 고정 시간 교육의 한계와 짧은 학습 단위 연구 |
| 0:45–1:05 | 3. 내일의 한국어 | 상황 음성, 역할극, 두 축 피드백, 재시도, 내일 문장 흐름 |
| 1:05–2:05 | live demo | 실제 microphone capture와 audio upload, fixture 응답으로 전체 interaction 완주 |
| 2:05–2:30 | 4. LLM이 필요한 자리 | 상황 구조화, 답변 기반 질문, 교정 우선순위 선택 |
| 2:30–3:00 | 5. 작동 범위와 검증 | 실제 동작과 fixture 구분, empty audio 422 양성 대조, state transition 검사 |
| 3:00–3:30 | 6. 내일 말할 수 있게 | 목적 전달 중심의 성공 기준과 마지막 문장 |

## slide별 설계

### 1. 내일 해야 할 통화

사용자 장면 한 문장과 전화 아이콘만 둔다. 제품 설명과 통계는 넣지 않는다. 발표자는 아이 결석을
알려야 하지만 한국어 통화를 피하고 싶은 이주민 부모의 내일을 20초 안에 설명한다.

### 2. 교재보다 먼저 닥치는 대화

국가데이터처의 외국인 취업자 약 101만 명을 크게 표시한다. 국립국어원 연구가 지적한 정규 집단
교육과 고정 시간 매체의 한계를 짧게 연결한다. `퇴근 후 10분`은 확정된 사용자 행동이 아니라 연구가
뒷받침하는 제품 가설로 표현한다. 출처 URL은 speaker notes에 남긴다.

### 3. 내일의 한국어

하나의 수평 흐름으로 실제 demo contract를 보여 준다. 입력은 현재 구현과 맞춰 `중국어 상황 음성`,
출력은 `내일 쓸 세 문장`으로 쓴다. role-play 중 교정은 `어휘·문법`과 `발음 전달도` 두 축이다.
국적만으로 발음 오류를 단정하지 않는 경계도 한 줄로 표시한다.

### live demo

slide deck에서 demo 버튼을 눌러 배포된 앱을 새 tab으로 연다. 시연자는 상황 음성, 한국어 첫 답변,
피드백, 같은 문장 재시도, 내일 카드까지 60초에 완주한다. network 또는 microphone 실패에 대비해
현재 fixture app을 그대로 사용하며, 응답 분석이 fixture라는 사실을 다음 slide에서 명시한다.

### 4. LLM이 필요한 자리

LLM 역할을 세 개로 제한한다. 자유로운 생활 목표를 rehearsal schema로 바꾸고, 사용자의 답에 맞춰
질문과 도움을 바꾸며, 실제 대화에서 먼저 고칠 내용을 고른다. 고정 script나 단순 번역만으로는 이
세 역할을 함께 수행할 수 없다는 차이를 설명한다. 현재 MVP에는 실제 model이 연결되지 않았음을
하단에 표시한다.

### 5. 작동 범위와 검증

왼쪽에는 실제 동작인 microphone capture, audio upload, browser state, retry flow를 둔다. 오른쪽에는
fixture인 STT, 어휘·문법 피드백, 발음 전달도 점수를 둔다. 검증 근거로 API 6건과 state transition
3건을 제시하되, 숫자만으로 신뢰를 주장하지 않는다. empty audio가 422로 실패하는 양성 대조와 잘못된
state transition이 거부되는 입력을 함께 보여 준다.

### 6. 내일 말할 수 있게

완벽한 한국어가 아니라 내일의 목적 전달이 성공 기준임을 한 문장으로 고정한다. 마지막 문장은
`한국어 전체를 오늘 가르치려 하지 않습니다. 내일 꼭 해야 할 한마디를 오늘 자기 목소리로 끝냅니다.`
로 끝낸다.

## visual system

- 제품과 같은 `#6046E8`, 흰색, 연한 보라색을 사용한다.
- `Noto Sans KR`, `Noto Sans SC`, system sans-serif 순서로 사용한다.
- title 48–64px, body 24px 이상을 기본으로 한다.
- dashboard형 card grid를 만들지 않는다. slide마다 한 장면과 한 주장만 둔다.
- 장식용 stock image는 사용하지 않는다. 제품 UI screenshot과 단순 typography를 중심으로 구성한다.
- 외부 통계와 연구 출처는 해당 slide의 notes에 기록한다.

## interaction과 fallback

- `ArrowRight`, `Space`, `ArrowLeft`로 이동한다.
- 현재 slide와 전체 slide 수, 발표 경과 시간을 작게 표시한다.
- demo URL은 query parameter 또는 상단 상수 한 곳에서 바꿀 수 있게 한다.
- demo가 열리지 않으면 slide 3의 제품 UI screenshot과 slide 5의 실제/fixture 범위로 발표를 계속한다.
- reduced motion 설정에서는 transition을 제거한다.

## 검증

1. browser에서 16:9와 1280×720 viewport를 각각 render한다.
2. 모든 slide의 overflow와 최소 font size를 확인한다.
3. keyboard navigation과 demo link를 직접 누른다.
4. 발표 대본을 stopwatch로 재서 3분 30초 이내인지 확인한다.
5. 출처 문구와 현재 구현을 `docs/product-brief.md`, `CODEX_LOG.md`, test code에 대조한다.
6. fixture를 실제 AI 결과처럼 읽는 문구가 없는지 검색한다.

## 범위 밖

- 새로운 제품 기능과 실제 LLM 연결
- 모바일 발표 화면
- login, history, settings
- 검증하지 않은 사용자 인터뷰 결과
- fixture 점수를 실제 사용자 성과로 해석하는 주장
