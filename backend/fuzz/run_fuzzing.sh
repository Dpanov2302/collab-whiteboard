#!/usr/bin/env sh
set -eu

BASE_URL="${BASE_URL:-http://localhost:8000}"
TOKEN="${TOKEN:-}"
EXAMPLES="${EXAMPLES:-100}"
OUTPUT_FILE="${OUTPUT_FILE:-reports/fuzzing-output.txt}"

mkdir -p "$(dirname "$OUTPUT_FILE")"

set +e
if [ -n "$TOKEN" ]; then
  schemathesis run "$BASE_URL/api/openapi.json" \
    --experimental=openapi-3.1 \
    --checks all \
    --hypothesis-max-examples="$EXAMPLES" \
    --header "Authorization: Bearer $TOKEN" \
    > "$OUTPUT_FILE" 2>&1
else
  schemathesis run "$BASE_URL/api/openapi.json" \
    --experimental=openapi-3.1 \
    --checks all \
    --hypothesis-max-examples="$EXAMPLES" \
    > "$OUTPUT_FILE" 2>&1
fi
STATUS=$?
set -e

cat "$OUTPUT_FILE"
exit "$STATUS"
