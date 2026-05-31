#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export REPO_PROVIDER="github"
export REPO_CONFIG_FILE="${SCRIPT_DIR}/repo_rover_runner.github.env"

echo "Running GitHub connectivity check using ${REPO_CONFIG_FILE}"
"${SCRIPT_DIR}/test_ping_repo.sh"
echo "GitHub connectivity check passed."
