#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export REPO_PROVIDER="bitbucket"
export REPO_CONFIG_FILE="${SCRIPT_DIR}/repo_rover_runner.bitbucket.env"

echo "Running Bitbucket connectivity check using ${REPO_CONFIG_FILE}"
"${SCRIPT_DIR}/test_ping_repo.sh"
echo "Bitbucket connectivity check passed."
