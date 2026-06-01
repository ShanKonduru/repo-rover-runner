#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

VENV_PYTHON="${SCRIPT_DIR}/.venv/bin/python"
VENV_ACTIVATE="${SCRIPT_DIR}/.venv/bin/activate"
if [ ! -x "${VENV_PYTHON}" ]; then
    echo "[INFO] Workspace virtual environment not found. Creating .venv..."
    if command -v python3 >/dev/null 2>&1; then
        python3 -m venv "${SCRIPT_DIR}/.venv"
    else
        python -m venv "${SCRIPT_DIR}/.venv"
    fi
fi

if [ ! -f "${VENV_ACTIVATE}" ]; then
    echo "[ERROR] Could not find virtual environment activation script: ${VENV_ACTIVATE}"
    exit 1
fi

# shellcheck disable=SC1091
source "${VENV_ACTIVATE}"

python -m pip install --upgrade pip setuptools wheel
python -m pip install -r "${SCRIPT_DIR}/requirements-dev.txt"

if [ ! -x "${SCRIPT_DIR}/bin/gitleaks" ] && [ ! -f "${SCRIPT_DIR}/bin/gitleaks.exe" ] && ! command -v gitleaks >/dev/null 2>&1; then
    echo "[WARN] gitleaks CLI was not found on PATH."
    echo "[WARN] Place gitleaks under ${SCRIPT_DIR}/bin or install it (for example, brew install gitleaks)."
fi

echo "Dev dependencies installed successfully in .venv."
