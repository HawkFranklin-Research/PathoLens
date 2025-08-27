#!/usr/bin/env bash
set -euo pipefail

HOST=${HOST:-http://localhost:8081}
BODY_FILE=${1:-"$(dirname "$0")/predict_example.json"}

curl -sS -X POST \
  -H 'Content-Type: application/json' \
  --data-binary @"${BODY_FILE}" \
  "${HOST}/predict" | jq .

