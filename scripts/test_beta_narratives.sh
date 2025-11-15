#!/usr/bin/env bash
set -euo pipefail

# Beta validation: smoke-test core user journeys against the Kernel API
# Requirements: curl; Python available for JSON parsing (jq not required)

BASE_URL="${BASE_URL:-http://127.0.0.1:8001}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8001}"
AUTH_HEADER="Authorization: Bearer demo-tenant"

echo "[beta-check] Using BASE_URL=${BASE_URL}"

fail() {
	echo "[beta-check][FAIL] $1" >&2
	cleanup
	exit 1
}

pass() {
	echo "[beta-check][OK] $1"
}

SERVER_PID=""
cleanup() {
	if [ -n "${SERVER_PID}" ] && kill -0 "${SERVER_PID}" 2>/dev/null; then
		echo "[beta-check] Stopping temporary server (pid=${SERVER_PID})..."
		kill "${SERVER_PID}" || true
		wait "${SERVER_PID}" 2>/dev/null || true
	fi
}
trap cleanup EXIT

is_listening() {
	python - <<PY
import socket, sys
s=socket.socket()
try:
		s.settimeout(0.5)
		s.connect(("${HOST}", int(${PORT})))
		print("1")
except Exception:
		print("0")
finally:
		s.close()
PY
}

# Start a temporary server if not already listening
if [ "$(is_listening)" != "1" ]; then
	echo "[beta-check] No server on ${HOST}:${PORT}. Starting a temporary uvicorn..."
	if [ -x "/Users/balu/Projects/dyocense/.venv/bin/uvicorn" ]; then
		PYTHONPATH=. /Users/balu/Projects/dyocense/.venv/bin/uvicorn backend.main:app --host "${HOST}" --port "${PORT}" &
	else
		PYTHONPATH=. python -m uvicorn backend.main:app --host "${HOST}" --port "${PORT}" &
	fi
	SERVER_PID=$!
	# Wait until healthy
	for i in {1..30}; do
		code=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/health" || true)
		if [ "${code}" = "200" ]; then
			pass "server is up"
			break
		fi
		sleep 0.3
	done
	if [ "${code}" != "200" ]; then
		fail "server failed to start"
	fi
fi

TMP_COMPILE=$(mktemp)
echo "[beta-check] POST /v1/compile..."
curl -s -S -X POST "${BASE_URL}/v1/compile" \
	-H "Content-Type: application/json" \
	-H "${AUTH_HEADER}" \
	-d '{"goal":"Reduce cost","tenant_id":"demo","project_id":"test-beta"}' \
	-o "${TMP_COMPILE}" || fail "compile request errored"

export TMP_COMPILE
OPS_JSON=$(python - <<'PY'
import sys, json, os
path = os.environ.get('TMP_COMPILE')
with open(path, 'r', encoding='utf-8') as f:
		data=json.load(f)
ops=data.get("ops")
print(json.dumps(ops if ops is not None else []))
PY
)

if [ "${OPS_JSON}" = "[]" ] || [ -z "${OPS_JSON}" ]; then
	fail "compile returned empty ops"
fi
pass "compile produced ops"

# 2) Optimise: run optimiser on ops
echo "[beta-check] POST /v1/optimise..."
OPTIMISE_CODE=$(curl -s -S -o /dev/null -w "%{http_code}" -X POST "${BASE_URL}/v1/optimise" \
	-H "Content-Type: application/json" \
	-H "${AUTH_HEADER}" \
	-d "{\"ops\": ${OPS_JSON}}") || fail "optimise request errored"

[ "${OPTIMISE_CODE}" = "200" ] || fail "optimise returned ${OPTIMISE_CODE}"
pass "optimise accepted ops"

# 3) Catalog: verify catalog is reachable
echo "[beta-check] GET /v1/catalog..."
CATALOG_CODE=$(curl -s -S -o /dev/null -w "%{http_code}" -X GET "${BASE_URL}/v1/catalog" -H "${AUTH_HEADER}") || fail "catalog request errored"
[ "${CATALOG_CODE}" = "200" ] || fail "catalog returned ${CATALOG_CODE}"
pass "catalog returns 200"

# 4) Health Score: verify minimal payload shape
TENANT_ID="demo"
echo "[beta-check] GET /v1/tenants/${TENANT_ID}/health-score..."
TMP_HEALTH=$(mktemp)
export TMP_HEALTH
curl -s -S -X GET "${BASE_URL}/v1/tenants/${TENANT_ID}/health-score" -H "${AUTH_HEADER}" -o "${TMP_HEALTH}" || fail "health-score request errored"

python - <<'PY' || exit 1
import json, os, sys
path = os.environ.get('TMP_HEALTH')
try:
	with open(path, 'r', encoding='utf-8') as f:
		data = json.load(f)
	assert isinstance(data.get('score'), (int, float)), 'score missing/not number'
	assert 'breakdown' in data and isinstance(data['breakdown'], dict), 'breakdown missing'
	bd = data['breakdown']
	# Accept presence of required availability flags
	for k in ['revenue_available','operations_available','customer_available']:
		assert k in bd, f'{k} missing in breakdown'
	# Optional numeric components if present
	for k in ['revenue','operations','customer']:
		if k in bd:
			assert isinstance(bd[k], (int, float)), f'{k} not numeric'
	assert 'last_updated' in data, 'last_updated missing'
	assert 'period_days' in data, 'period_days missing'
	print('[beta-check][OK] health-score payload shape is valid')
except AssertionError as e:
	print(f"[beta-check][FAIL] health-score validation failed: {e}", file=sys.stderr)
	sys.exit(1)
except Exception as e:
	print(f"[beta-check][FAIL] health-score error: {e}", file=sys.stderr)
	sys.exit(1)
PY

echo "[beta-check] All core checks passed."
