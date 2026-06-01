# Repo Rover Runner

```text
+----------------------------+
|      REPO ROVER RUNNER     |
+----------------------------+
```

Repo Rover Runner is a local automation toolkit that standardizes a small set of git workflows for both GitHub and Bitbucket repositories.

It is built around a Python CLI plus Windows (.bat) and Linux/macOS (.sh) helper scripts.

Script help documents are available under `docs/utilities/`.

## What This Workspace Is Doing

This project automates these tasks against a remote git repository:

1. Connectivity check (ping remote)
2. Clone if needed
3. Create or attach to a working branch
4. List local and remote branches
5. Copy one or more files/folders into the repo
6. Commit and push to remote branch

It does not call GitHub or Bitbucket REST APIs directly. It relies on standard git commands, so it works with either provider as long as the remote URL and credentials are valid.

## Core CLI

Primary entrypoint:

```bash
python repo_rover_runner_client.py --help
```

Installed command aliases (Windows installs `.exe` launchers):

```bash
repo-rover-runner --help
rrr --help
```

Legacy compatibility wrapper:

```bash
python repo_rover_runner_cli.py --help
```

## MCP Server

The project now ships an MCP stdio server that exposes the same core operations.

Start it with:

```bash
repo-rover-runner-mcp
```

Exposed MCP tools:

1. `ping_repo`
2. `clone_repo`
3. `use_branch`
4. `list_branches`
5. `push_files`

### MCP Client JSON Configurations

The MCP server uses stdio transport, so most clients use a JSON entry under `mcpServers`.

Minimal server command:

```json
{
   "mcpServers": {
      "repo-rover-runner": {
         "command": "repo-rover-runner-mcp"
      }
   }
}
```

If the command is not on PATH, use an explicit Python executable and script path.

Windows example (project-local virtual environment):

```json
{
   "mcpServers": {
      "repo-rover-runner": {
         "command": "C:\\MyProjects\\repo-rover-runner\\.venv\\Scripts\\python.exe",
         "args": [
            "C:\\MyProjects\\repo-rover-runner\\repo_rover_runner_mcp_server.py"
         ]
      }
   }
}
```

Linux/macOS example:

```json
{
   "mcpServers": {
      "repo-rover-runner": {
         "command": "/path/to/repo-rover-runner/.venv/bin/python",
         "args": [
            "/path/to/repo-rover-runner/repo_rover_runner_mcp_server.py"
         ]
      }
   }
}
```

#### Client-Specific Examples

Claude Desktop (`claude_desktop_config.json`):

```json
{
   "mcpServers": {
      "repo-rover-runner": {
         "command": "repo-rover-runner-mcp",
         "env": {
            "REPO_PROVIDER": "github",
            "GITHUB_TOKEN": "${GITHUB_TOKEN}",
            "GIT_USERNAME": "x-access-token"
         }
      }
   }
}
```

VS Code MCP config (settings.json):

```json
{
   "mcp": {
      "servers": {
         "repo-rover-runner": {
            "command": "C:\\MyProjects\\repo-rover-runner\\.venv\\Scripts\\python.exe",
            "args": [
               "C:\\MyProjects\\repo-rover-runner\\repo_rover_runner_mcp_server.py"
            ],
            "env": {
               "REPO_PROVIDER": "auto"
            }
         }
      }
   }
}
```

If `repo-rover-runner-mcp` is on PATH, you can also use:

```json
{
   "mcp": {
      "servers": {
         "repo-rover-runner": {
            "command": "repo-rover-runner-mcp",
            "env": {
               "REPO_PROVIDER": "auto"
            }
         }
      }
   }
}
```

Cursor/Cline-style MCP config:

```json
{
   "mcpServers": {
      "repo-rover-runner": {
         "command": "repo-rover-runner-mcp",
         "args": [],
         "env": {
            "REPO_PROVIDER": "auto"
         }
      }
   }
}
```

Generic host config with explicit working defaults:

```json
{
   "mcpServers": {
      "repo-rover-runner": {
         "command": "repo-rover-runner-mcp",
         "env": {
            "REPO_PROVIDER": "bitbucket",
            "BITBUCKET_USERNAME": "your-user",
            "BITBUCKET_APP_PASSWORD": "your-app-password"
         }
      }
   }
}
```

#### Recommended Environment Variables for MCP Clients

Most clients allow per-server `env` values. Use those to avoid embedding credentials in URLs.

GitHub HTTPS auth:

1. `REPO_PROVIDER=github`
2. `GITHUB_TOKEN=<token>`
3. `GIT_USERNAME=x-access-token` (optional; default is already `x-access-token`)

Bitbucket HTTPS auth:

1. `REPO_PROVIDER=bitbucket`
2. `BITBUCKET_USERNAME=<username>` (or `GIT_USERNAME`)
3. `BITBUCKET_APP_PASSWORD=<app-password>` (or `BITBUCKET_TOKEN`)

Notes:

1. Keep secrets out of committed files.
2. Prefer environment-variable expansion supported by your MCP host.
3. If your host cannot expand `${VAR}`, set values directly in that host's secure secret settings.

Supported subcommands:

1. `ping`
2. `clone`
3. `use-branch`
4. `list-branches`
5. `push-files`

### Command Behavior Summary

`ping`

- Runs `git ls-remote <repo-url> HEAD`

`clone`

- Clones into destination folder
- Fails if destination exists and is not empty

`use-branch`

- Fetches remote first
- Reuses local branch if it exists
- Otherwise tracks remote branch if it exists
- Otherwise creates from remote base branch
- Otherwise creates from local base branch
- If repository has no commits, creates orphan branch

`list-branches`

- Fetches remote first
- Prints local and/or remote branches by scope: `all | local | remote`

`push-files`

- Ensures branch exists (same logic as `use-branch`)
- Copies provided files/folders into target directory in repo
- Stages copied paths only
- If no staged diff, exits without commit/push
- Otherwise commits and pushes with upstream tracking

## Authentication Model

For SSH remotes, normal git SSH auth applies.

For HTTPS remotes, the CLI and scripts support temporary `GIT_ASKPASS` credentials via environment variables:

- GitHub: `GITHUB_TOKEN` and optional `GIT_USERNAME` (default `x-access-token`)
- Bitbucket: `BITBUCKET_APP_PASSWORD` (or `BITBUCKET_TOKEN`) and `BITBUCKET_USERNAME` (or `GIT_USERNAME`)

Provider selection:

- `REPO_PROVIDER=github`
- `REPO_PROVIDER=bitbucket`
- `REPO_PROVIDER=auto` (default): prefers GitHub token if present, otherwise Bitbucket credentials

The project does not persist credentials.

## Configuration Files

Preferred provider-specific files:

- `repo_rover_runner.github.env`
- `repo_rover_runner.bitbucket.env`

Legacy combined template:

- `repo_rover_runner.env.example`
- optional runtime file: `repo_rover_runner.env`

Common required variables:

- `REPO_URL`
- `LOCAL_REPO_PATH`
- `TARGET_BRANCH`

Common optional variables:

- `BASE_BRANCH` (default `main`)
- `REMOTE` (default `origin`)
- `TARGET_DIR` (default `integration-tests`)
- `COMMIT_MESSAGE`
- `BRANCH_TO_LIST`

Script config resolution order:

1. `REPO_CONFIG_FILE` if provided
2. provider-specific file if `REPO_PROVIDER` set
3. auto-fallback: `repo_rover_runner.bitbucket.env`, then `repo_rover_runner.github.env`, then `repo_rover_runner.env`

## Helper Scripts

The workspace includes paired scripts for Windows and Linux/macOS to run end-to-end checks quickly.

Main scripted operations:

1. `test_ping_repo` - remote reachability/auth check
2. `create_new_branch` - clone-if-needed then `use-branch`
3. `test_list_branches` - branch listing
4. `test_use_branch` - branch checkout/create flow
5. `list_files_in_branch` - file listing from a branch ref
6. `test_push_dummy` - push `dummy_payload.txt`

One-command suites:

- `run_github_tests.bat` / `run_github_tests.sh`
- `run_bitbucket_tests.bat` / `run_bitbucket_tests.sh`

Connectivity-only suites:

- `run_github_connectivity.bat` / `run_github_connectivity.sh`
- `run_bitbucket_connectivity.bat` / `run_bitbucket_connectivity.sh`

## Quick Start

1. Create and fill one config file (`repo_rover_runner.github.env` or `repo_rover_runner.bitbucket.env`).
2. Set provider if needed: `REPO_PROVIDER=github` or `REPO_PROVIDER=bitbucket`.
3. Run one command:

Windows:

```bat
run_github_tests.bat
```

or

```bat
run_bitbucket_tests.bat
```

Linux/macOS:

```bash
./run_github_tests.sh
```

or

```bash
./run_bitbucket_tests.sh
```

## Project Structure

Python package:

- `repo_rover_runner/interfaces.py`: operation contract
- `repo_rover_runner/operations.py`: shared git implementation and provider classes
- `repo_rover_runner/factory.py`: provider selection
- `repo_rover_runner/auth.py`: temporary HTTPS askpass setup and env resolution
- `repo_rover_runner/exceptions.py`: custom error type

CLI:

- `repo_rover_runner_client.py`: main CLI
- `repo_rover_runner_cli.py`: legacy wrapper to main CLI

Tests:

- `tests/test_auth.py`
- `tests/test_factory.py`
- `tests/test_operations.py`
- `tests/test_cli_client.py`

## Unit Tests

Windows:

```bat
run_repo_rover_runner_unit_tests.bat
```

Linux/macOS:

```bash
./run_repo_rover_runner_unit_tests.sh
```

The test runner executes unittest with coverage and prints a coverage report.

## Security Reports

Dev/security dependencies are available through either:

```bash
pip install -r requirements-dev.txt
```

or:

```bash
pip install ".[dev]"
```

Generate security reports:

Windows:

```bat
run_security_reports.bat
```

Linux/macOS:

```bash
./run_security_reports.sh
```

All generated security artifacts are written under:

1. `test_results/Secutiry_reports/pip_audit_report.json`
2. `test_results/Secutiry_reports/bandit_report.json`
3. `test_results/Secutiry_reports/gitleaks_report.json`
4. `test_results/Secutiry_reports/pip_audit_report.html`
5. `test_results/Secutiry_reports/bandit_report.html`
6. `test_results/Secutiry_reports/gitleaks_report.html`
7. `test_results/Secutiry_reports/security_consolidated.html`

`sec-report-kit` is used when available to convert JSON reports to HTML, with an automatic built-in HTML fallback to guarantee report generation.

## GitHub Actions Workflows

The repository now includes these workflows under `.github/workflows/`:

1. `ci.yml`
2. `publish-testpypi.yml`
3. `publish-pypi.yml`

### CI and Security

`ci.yml` runs on push and pull request and includes:

1. Unit tests with coverage
2. Dependency vulnerability scan with `pip-audit`
3. Static security scan with `bandit`
4. Secret scan with `gitleaks`

### TestPyPI Publish

`publish-testpypi.yml` publishes to TestPyPI:

1. Manually via `workflow_dispatch`
2. Automatically for pre-release tags like:
   1. `vX.Y.Z-rcN`
   2. `vX.Y.Z-betaN`
   3. `vX.Y.Z-alphaN`

### PyPI Publish

`publish-pypi.yml` publishes to PyPI:

1. Manually via `workflow_dispatch`
2. Automatically when a GitHub Release is published

### Required Repository Setup for Publishing

Both publish workflows use trusted publishing (`id-token: write`) with `pypa/gh-action-pypi-publish`.

Configure these environments in GitHub repository settings:

1. `testpypi`
2. `pypi`

Then configure trusted publisher entries in TestPyPI/PyPI for this repository and workflow files.
