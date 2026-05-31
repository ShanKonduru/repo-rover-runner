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
TARGET_DIR="${TARGET_DIR:-integration-tests}"
COMMIT_MESSAGE="${COMMIT_MESSAGE:-Add dummy file from repo-rover-runner test script}"

REPO_PATH_ABS="${SCRIPT_DIR}/${LOCAL_REPO_PATH}"

ASKPASS_FILE=""
setup_https_auth() {
  if [[ "${REPO_URL}" != https://* ]]; then
    return 0
  fi

  local provider="${REPO_PROVIDER:-auto}"
  local auth_user=""
  local auth_token=""

  if [ "${provider}" = "github" ]; then
    if [ -z "${GITHUB_TOKEN:-}" ]; then
      echo "ERROR: REPO_PROVIDER=github requires GITHUB_TOKEN"
      exit 1
    fi
    auth_user="${GIT_USERNAME:-x-access-token}"
    auth_token="${GITHUB_TOKEN}"
  elif [ "${provider}" = "bitbucket" ]; then
    auth_user="${BITBUCKET_USERNAME:-${GIT_USERNAME:-}}"
    auth_token="${BITBUCKET_APP_PASSWORD:-${BITBUCKET_TOKEN:-}}"
    if [ -z "${auth_token}" ]; then
      echo "ERROR: REPO_PROVIDER=bitbucket requires BITBUCKET_APP_PASSWORD (or BITBUCKET_TOKEN)"
      exit 1
    fi
    if [ -z "${auth_user}" ]; then
      echo "ERROR: BITBUCKET_USERNAME (or GIT_USERNAME) is required for Bitbucket HTTPS auth"
      exit 1
    fi
  elif [ "${provider}" = "auto" ] || [ -z "${provider}" ]; then
    if [ -n "${GITHUB_TOKEN:-}" ]; then
      auth_user="${GIT_USERNAME:-x-access-token}"
      auth_token="${GITHUB_TOKEN}"
    elif [ -n "${BITBUCKET_APP_PASSWORD:-}" ] || [ -n "${BITBUCKET_TOKEN:-}" ]; then
      auth_user="${BITBUCKET_USERNAME:-${GIT_USERNAME:-}}"
      auth_token="${BITBUCKET_APP_PASSWORD:-${BITBUCKET_TOKEN:-}}"
      if [ -z "${auth_user}" ]; then
        echo "ERROR: BITBUCKET_USERNAME (or GIT_USERNAME) is required for Bitbucket HTTPS auth"
        exit 1
      fi
    else
      echo "ERROR: HTTPS remote detected but no token provided (GITHUB_TOKEN, BITBUCKET_APP_PASSWORD, or BITBUCKET_TOKEN)"
      exit 1
    fi
  else
    echo "ERROR: REPO_PROVIDER must be auto, github, or bitbucket"
    exit 1
  fi

  ASKPASS_FILE="$(mktemp "${TMPDIR:-/tmp}/repo_rover_runner_askpass.XXXXXX")"
  cat > "${ASKPASS_FILE}" <<'EOF'
#!/usr/bin/env bash
prompt="$1"
case "$prompt" in
  *sername*|*Username*) printf '%s\n' "${RB_AUTH_USER}" ;;
  *assword*|*Password*) printf '%s\n' "${RB_AUTH_TOKEN}" ;;
  *) printf '\n' ;;
esac
EOF
  chmod 700 "${ASKPASS_FILE}"

  export RB_AUTH_USER="${auth_user}"
  export RB_AUTH_TOKEN="${auth_token}"
  export GIT_ASKPASS="${ASKPASS_FILE}"
  export GIT_TERMINAL_PROMPT=0
}

cleanup_auth() {
  if [ -n "${ASKPASS_FILE}" ] && [ -f "${ASKPASS_FILE}" ]; then
    rm -f "${ASKPASS_FILE}"
  fi
}

trap cleanup_auth EXIT
setup_https_auth

if [ ! -d "${REPO_PATH_ABS}/.git" ]; then
  python "${SCRIPT_DIR}/repo_rover_runner_cli.py" clone --repo-url "${REPO_URL}" --dest "${REPO_PATH_ABS}"
fi

python "${SCRIPT_DIR}/repo_rover_runner_cli.py" push-files \
  --repo-path "${REPO_PATH_ABS}" \
  --branch "${TARGET_BRANCH}" \
  --files "${SCRIPT_DIR}/dummy_payload.txt" \
  --target-dir "${TARGET_DIR}" \
  --commit-message "${COMMIT_MESSAGE}" \
  --base-branch "${BASE_BRANCH}" \
  --remote "${REMOTE}"
