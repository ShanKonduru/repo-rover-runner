#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

python -m coverage erase
python -m coverage run --rcfile "${SCRIPT_DIR}/.coveragerc" -m unittest discover -s tests -p "test_*.py"
python -m coverage report --rcfile "${SCRIPT_DIR}/.coveragerc"

echo "Unit tests passed with 100% coverage."
