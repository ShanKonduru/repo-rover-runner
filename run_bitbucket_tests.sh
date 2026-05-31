#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export REPO_PROVIDER="bitbucket"
export REPO_CONFIG_FILE="${SCRIPT_DIR}/repo_rover_runner.bitbucket.env"

echo "Running Bitbucket test sequence using ${REPO_CONFIG_FILE}"

"${SCRIPT_DIR}/test_ping_repo.sh"
"${SCRIPT_DIR}/create_new_branch.sh"
"${SCRIPT_DIR}/test_list_branches.sh"
"${SCRIPT_DIR}/test_use_branch.sh"
"${SCRIPT_DIR}/list_files_in_branch.sh"
"${SCRIPT_DIR}/test_push_dummy.sh"

echo "Bitbucket test sequence completed successfully."
