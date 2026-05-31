#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -n "${REPO_CONFIG_FILE:-}" ]; then
  ENV_FILE="${REPO_CONFIG_FILE}"
elif [ "${REPO_PROVIDER:-}" = "github" ]; then
  ENV_FILE="${SCRIPT_DIR}/repo_rover_runner.github.env"
elif [ "${REPO_PROVIDER:-}" = "bitbucket" ]; then
  ENV_FILE="${SCRIPT_DIR}/repo_rover_runner.bitbucket.env"
elif [ -f "${SCRIPT_DIR}/repo_rover_runner.bitbucket.env" ]; then
  ENV_FILE="${SCRIPT_DIR}/repo_rover_runner.bitbucket.env"
elif [ -f "${SCRIPT_DIR}/repo_rover_runner.github.env" ]; then
  ENV_FILE="${SCRIPT_DIR}/repo_rover_runner.github.env"
else
  ENV_FILE="${SCRIPT_DIR}/repo_rover_runner.env"
fi

if [ ! -f "${ENV_FILE}" ]; then
  echo "ERROR: Missing ${ENV_FILE}. Provide REPO_CONFIG_FILE or create repo_rover_runner.github.env/repo_rover_runner.bitbucket.env."
  exit 1
fi

set -a
. "${ENV_FILE}"
set +a

: "${REPO_URL:?REPO_URL missing in selected config file}"
: "${LOCAL_REPO_PATH:?LOCAL_REPO_PATH missing in selected config file}"
: "${TARGET_BRANCH:?TARGET_BRANCH missing in selected config file}"

BASE_BRANCH="${BASE_BRANCH:-main}"
REMOTE="${REMOTE:-origin}"
REPO_PATH_ABS="${SCRIPT_DIR}/${LOCAL_REPO_PATH}"

if [ ! -d "${REPO_PATH_ABS}/.git" ]; then
  python "${SCRIPT_DIR}/repo_rover_runner_cli.py" clone --repo-url "${REPO_URL}" --dest "${REPO_PATH_ABS}"
fi

python "${SCRIPT_DIR}/repo_rover_runner_cli.py" use-branch \
  --repo-path "${REPO_PATH_ABS}" \
  --branch "${TARGET_BRANCH}" \
  --base-branch "${BASE_BRANCH}" \
  --remote "${REMOTE}"
