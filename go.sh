#!/bin/bash
# 해커톤 Codex 실행 — 격리된 CODEX_HOME (teammode 훅 없음, 개인 프로필 없음)
cd "$(dirname "$0")" || exit 1
export CODEX_HOME="$PWD/.codex-home"
exec codex "$@"
