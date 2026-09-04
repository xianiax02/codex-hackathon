#!/bin/bash
# Codex 세션 설정 점검 — API 호출 없음.
# codex debug prompt-input 은 모델에 실제로 들어가는 입력을 그대로 뱉는다.
cd "$(dirname "$0")" || exit 1

export CODEX_HOME="$PWD/.codex-home"
J=$(mktemp)
codex debug prompt-input 2>/dev/null > "$J" || { echo "codex debug 실패"; exit 1; }

pass=0; fail=0
chk() { # 이름 / 기대(yes|no) / 패턴
  n=$(grep -c "$3" "$J")
  if [ "$2" = yes ]; then [ "$n" -gt 0 ] && r=OK || r=FAIL
  else [ "$n" -eq 0 ] && r=OK || r=FAIL; fi
  [ "$r" = OK ] && pass=$((pass+1)) || fail=$((fail+1))
  printf '  [%s] %-34s (%d건)\n' "$r" "$1" "$n"
}

echo "== 들어가야 하는 것 =="
chk "전역 규칙 (.codex-home/AGENTS.md)" yes "양성 대조를 먼저"
chk "레포 규칙 (AGENTS.md)"          yes "60초 데모 대본이 스펙"
chk "제품 미정 명시"                  yes "제품은 아직 정해지지 않았다"
chk "systematic-debugging 스킬"       yes "systematic-debugging"

echo "== 들어가면 안 되는 것 =="
chk "제품 전제 (뉴스/차집합)"        no "차집합"
chk "전화번호"                        no "010-7255-1996"
chk "전체 프로필 블록"                no "personal-profile"
chk "여권 영문명"                     no "LIM / JUNHYOUN"
chk "brainstorming (hard gate)"       no "brainstorming"
chk "teammode 스킬"                   no "tm-memory"

echo "== 검사기 자체 점검 (양성 대조) =="
# 반드시 검출돼야 하는 문자열. 0건이면 검사기가 고장난 것이지 통과가 아니다.
n=$(grep -c "skills_instructions" "$J")
if [ "$n" -gt 0 ]; then echo "  [OK] 검사기 작동 확인"; else
  echo "  [!!] 검사기 고장 — 위 결과 전부 무효"; fail=$((fail+1)); fi

echo
echo "prompt 총 크기: $(wc -c < "$J") bytes"
echo "결과: ${pass} OK / ${fail} FAIL"
[ -d .git ] && echo "git repo: 예 (개인정보 차단됨)" || echo "git repo: 아니오 ← git init 필요!"
rm -f "$J"
[ "$fail" -eq 0 ]
