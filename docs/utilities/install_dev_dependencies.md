# install_dev_dependencies

Installs Python development dependencies into the workspace virtual environment (`.venv`).

Scripts:

- Windows: `install_dev_dependencies.bat`
- Linux/macOS: `install_dev_dependencies.sh`

## What It Does

1. Changes to the repository root (the script directory).
2. Ensures `.venv` exists (creates it if missing).
3. Activates `.venv`.
4. Upgrades `pip`, `setuptools`, and `wheel` in `.venv`.
5. Installs everything from `requirements-dev.txt`.

## Usage

Windows:

```bat
install_dev_dependencies.bat
```

Linux/macOS:

```bash
./install_dev_dependencies.sh
```

## Notes

- On Linux/macOS, run `chmod +x install_dev_dependencies.sh` once if needed.
- The scripts target `.venv` only, so global Python packages are not modified.
- `gitleaks` is an external CLI dependency and is not installed by pip. Install it separately and ensure it is available on `PATH`.
