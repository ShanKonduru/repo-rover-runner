# Worktop Sample Integration (React + Node + Python)

This sample shows how a React app can trigger the existing `repo-rover-runner` Python code to:

1. Create/use a branch
2. Copy generated scripts into the repo
3. Commit and push to GitHub/Bitbucket

The browser never sees Git credentials. Tokens stay server-side in Node/Python environment variables.

## Architecture

- Frontend: React (Vite)
- Backend: Node + Express
- Git engine: existing Python CLI (`repo_rover_runner_client.py`)

Flow:

1. React loads GitHub or Bitbucket defaults from the backend provider config endpoint
2. React sends `POST /api/jobs/publish-generated-scripts`
3. Node validates input and enqueues a job
4. Node loads the matching env file for the selected provider
5. Node invokes Python CLI commands (`clone`, `use-branch`, `push-files`)
6. React polls `GET /api/jobs/:jobId`

## Key Gaps Covered

- Queueing: in-memory sequential queue in backend
- Branch policy: `worktop/<branchHint>/<utcTimestamp>`
- Repo allow-list: `ALLOWED_REPO_PREFIXES`
- Validation: provider/repo/path checks
- Secret safety: no token fields accepted from frontend payload
- Provider-specific env loading: GitHub uses `repo_rover_runner.github.env`, Bitbucket uses `repo_rover_runner.bitbucket.env`

## Folder Structure

- `backend/`: Express API and Python CLI orchestration
- `frontend/`: React UI that submits and polls publish jobs

## Prerequisites

1. Python virtual environment for this repository is available
2. Node.js 18+ installed
3. Git installed and on PATH
4. Auth environment variables set for target provider

## Backend Setup

From `examples/worktop-sample/backend`:

```bash
npm install
```

Set environment variables (copy from `.env.example`).

Windows PowerShell example:

```powershell
$env:PYTHON_BIN="C:\MyProjects\repo-rover-runner\.venv\Scripts\python.exe"
$env:REPO_PROVIDER="auto"
$env:GITHUB_TOKEN="<token>"
$env:GIT_USERNAME="x-access-token"
$env:ALLOWED_REPO_PREFIXES="https://github.com/your-org/,https://bitbucket.org/your-org/"
npm start
```

Backend runs at `http://localhost:4070`.

## Frontend Setup

From `examples/worktop-sample/frontend`:

```bash
npm install
npm run dev
```

Open the shown Vite URL (typically `http://localhost:5173`).

## Sample Payload

```json
{
  "provider": "github",
  "repoUrl": "https://github.com/your-org/your-repo.git",
  "localRepoPath": "C:/worktop/repos/your-repo",
  "generatedPath": "C:/MyProjects/repo-rover-runner/dummy_payload.txt",
  "targetDir": "tests/generated",
  "baseBranch": "main",
  "remote": "origin",
  "branchHint": "stlc-smoke",
  "commitMessage": "Worktop: add generated scripts for STLC smoke"
}
```

## Notes

- Current queue is in-memory for simplicity. Production should use Redis/SQS/etc.
- Current backend process-level environment is used for auth. Production should use a secure secret manager.
- For high concurrency, run each job in isolated workspaces/containers.
