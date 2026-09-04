#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/.."
smoke_port="${SMOKE_PORT:-8765}"
smoke_url="http://127.0.0.1:${smoke_port}"
log_file="$(mktemp /tmp/modu-korean-smoke.XXXXXX)"

OPENAI_API_KEY= .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port "$smoke_port" >"$log_file" 2>&1 &
server_pid=$!
cleanup() {
  kill "$server_pid" 2>/dev/null || true
}
trap cleanup EXIT

for _ in 1 2 3 4 5; do
  if curl --silent --fail "$smoke_url/api/health" >/dev/null; then
    break
  fi
  sleep 1
done

health="$(curl --silent --fail "$smoke_url/api/health")"
case "$health" in
  *'"analysis_mode":"fixture"'*) ;;
  *) echo "health response가 fixture mode를 밝히지 않음: $health"; exit 1 ;;
esac

empty_status="$(curl --silent --output /dev/null --write-out '%{http_code}' \
  --request POST --header 'Content-Type: audio/webm' --data-binary '' \
  "$smoke_url/api/context")"
test "$empty_status" = "422"

valid_context="$(curl --silent --fail --request POST \
  --header 'Content-Type: audio/webm' --data-binary 'recorded-audio' \
  "$smoke_url/api/context")"
case "$valid_context" in
  *'"teacher_question"'*) ;;
  *) echo "정상 audio가 rehearsal context를 만들지 못함"; exit 1 ;;
esac

valid_attempt="$(curl --silent --fail --request POST \
  --header 'Content-Type: audio/webm' --data-binary 'recorded-audio' \
  "$smoke_url/api/attempts?attempt=first")"
case "$valid_attempt" in
  *'"language"'*'"pronunciation"'*) ;;
  *) echo "정상 audio가 두 feedback 축을 만들지 못함"; exit 1 ;;
esac

curl --silent --fail "$smoke_url/" | grep -q 'id="context-record"'
echo "smoke OK: health fixture 표시, empty audio 422, context/feedback 응답, UI 제공"
