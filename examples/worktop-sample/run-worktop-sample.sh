#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$ROOT_DIR/../.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
load_env_file() {
  local env_path="$1"
  local line key value

  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%$'\r'}"
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" != *=* ]] && continue

    key="${line%%=*}"
    value="${line#*=}"

    key="${key//[[:space:]]/}"
    if [[ -n "$key" ]]; then
      export "$key=$value"
    fi
  done < "$env_path"
}

if [[ -n "${PYTHON_BIN:-}" ]]; then
  PYTHON_BIN="$PYTHON_BIN"
elif [[ -x "$REPO_ROOT/.venv/bin/python" ]]; then
  PYTHON_BIN="$REPO_ROOT/.venv/bin/python"
else
  PYTHON_BIN="$REPO_ROOT/.venv/Scripts/python.exe"
fi
BACKEND_PORT="${BACKEND_PORT:-4070}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

REPO_PROVIDER="${REPO_PROVIDER:-github}"
if [[ "$REPO_PROVIDER" == "bitbucket" ]]; then
  ENV_FILE="$REPO_ROOT/repo_rover_runner.bitbucket.env"
else
  ENV_FILE="$REPO_ROOT/repo_rover_runner.github.env"
fi

if [[ -f "$ENV_FILE" ]]; then
  load_env_file "$ENV_FILE"
fi

WORKTOP_REPO_URL="${WORKTOP_REPO_URL:-${REPO_URL:-}}"
WORKTOP_BASE_BRANCH="${WORKTOP_BASE_BRANCH:-${BASE_BRANCH:-main}}"
WORKTOP_REPO_DIR="${WORKTOP_REPO_DIR:-${LOCAL_REPO_PATH:-$ROOT_DIR/_tmp-repo}}"
WORKTOP_GENERATED_PATH="${WORKTOP_GENERATED_PATH:-$REPO_ROOT/dummy_payload.txt}"
WORKTOP_TARGET_DIR="${WORKTOP_TARGET_DIR:-${TARGET_DIR:-tests/generated}}"
WORKTOP_COMMIT_MESSAGE="${WORKTOP_COMMIT_MESSAGE:-${COMMIT_MESSAGE:-Worktop smoke test: add generated test script}}"
REPO_PROVIDER="${REPO_PROVIDER:-auto}"

case "$WORKTOP_REPO_DIR" in
  /*) ;;
  *) WORKTOP_REPO_DIR="$REPO_ROOT/$WORKTOP_REPO_DIR" ;;
esac

if [[ ! -x "$PYTHON_BIN" && ! -f "$PYTHON_BIN" ]]; then
  echo "ERROR: Python not found at $PYTHON_BIN" >&2
  exit 1
fi

if [[ ! -d "$BACKEND_DIR/node_modules" ]]; then
  echo "Installing backend dependencies..."
  (cd "$BACKEND_DIR" && npm install)
fi

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  echo "Installing frontend dependencies..."
  (cd "$FRONTEND_DIR" && npm install)
fi

WORKTOP_JOB_DIR="$ROOT_DIR/_tmp-job"
rm -rf "$WORKTOP_JOB_DIR" "$WORKTOP_REPO_DIR"

export PORT="$BACKEND_PORT"
export PYTHON_BIN="$PYTHON_BIN"
export REPO_PROVIDER

if [[ -z "$WORKTOP_REPO_URL" ]]; then
  echo "ERROR: WORKTOP_REPO_URL or REPO_URL was not found." >&2
  exit 1
fi

if [[ -z "${ALLOWED_REPO_PREFIXES:-}" ]]; then
  echo "WARNING: ALLOWED_REPO_PREFIXES is not set. The backend sample allows any repo URL."
fi

(
  cd "$BACKEND_DIR"
  npm start
) >"$ROOT_DIR/backend.log" 2>&1 &
BACKEND_PID=$!

(
  cd "$FRONTEND_DIR"
  npm run dev -- --host 127.0.0.1 --port "$FRONTEND_PORT"
) >"$ROOT_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!

trap 'kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true' EXIT

wait_for_http() {
  local url="$1"
  local attempts="${2:-30}"
  for _ in $(seq 1 "$attempts"); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  echo "ERROR: Service did not become ready: $url" >&2
  return 1
}

wait_for_http "http://127.0.0.1:$BACKEND_PORT/api/health" 30

echo "Submitting smoke-test publish job..."

JOB_RESPONSE="$WORKTOP_JOB_DIR/job-response.json"
curl -fsS -X POST "http://127.0.0.1:$BACKEND_PORT/api/jobs/publish-generated-scripts" \
  -H "Content-Type: application/json" \
  -d "$(cat <<JSON
{
  "provider": "${REPO_PROVIDER}",
  "repoUrl": "${WORKTOP_REPO_URL}",
  "localRepoPath": "${WORKTOP_REPO_DIR}",
  "generatedPath": "${WORKTOP_GENERATED_PATH}",
  "targetDir": "${WORKTOP_TARGET_DIR}",
  "baseBranch": "${WORKTOP_BASE_BRANCH}",
  "remote": "origin",
  "branchHint": "worktop-smoke",
  "commitMessage": "${WORKTOP_COMMIT_MESSAGE}"
}
JSON
)" > "$JOB_RESPONSE"

JOB_ID="$(python3 - <<'PY'
import json, sys
print(json.load(open(sys.argv[1]))["jobId"])
PY
"$JOB_RESPONSE")"

echo "Polling job status..."
for _ in $(seq 1 60); do
  JOB_STATE_FILE="$WORKTOP_JOB_DIR/job-state.json"
  curl -fsS "http://127.0.0.1:$BACKEND_PORT/api/jobs/$JOB_ID" > "$JOB_STATE_FILE"
  if grep -q '"status":"succeeded"' "$JOB_STATE_FILE"; then
    echo "Smoke test succeeded."
    cat "$JOB_STATE_FILE"
    exit 0
  fi
  if grep -q '"status":"failed"' "$JOB_STATE_FILE"; then
    echo "ERROR: Smoke test job failed." >&2
    cat "$JOB_STATE_FILE"
    exit 1
  fi
  sleep 2
done

echo "ERROR: Job did not finish in time." >&2
exit 1
