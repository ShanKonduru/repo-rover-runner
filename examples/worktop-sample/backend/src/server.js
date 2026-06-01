import cors from "cors";
import express from "express";
import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";

const app = express();
const port = Number(process.env.PORT || 4070);
const jobs = new Map();
const queue = [];
let processing = false;
const currentFilePath = fileURLToPath(import.meta.url);
const backendRoot = path.resolve(path.dirname(currentFilePath), "..");
const repoRoot = path.resolve(backendRoot, "..", "..", "..");
const providerEnvFiles = {
  github: path.join(repoRoot, "repo_rover_runner.github.env"),
  bitbucket: path.join(repoRoot, "repo_rover_runner.bitbucket.env")
};

app.use(cors());
app.use(express.json({ limit: "1mb" }));

function slug(input) {
  return String(input || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9._/-]+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^[-/.]+|[-/.]+$/g, "");
}

function nowStamp() {
  const d = new Date();
  const yyyy = d.getUTCFullYear();
  const mm = String(d.getUTCMonth() + 1).padStart(2, "0");
  const dd = String(d.getUTCDate()).padStart(2, "0");
  const hh = String(d.getUTCHours()).padStart(2, "0");
  const mi = String(d.getUTCMinutes()).padStart(2, "0");
  const ss = String(d.getUTCSeconds()).padStart(2, "0");
  return `${yyyy}${mm}${dd}-${hh}${mi}${ss}`;
}

function getAllowedRepoPrefixes() {
  return String(process.env.ALLOWED_REPO_PREFIXES || "")
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);
}

function parseEnvFile(filePath) {
  if (!fs.existsSync(filePath)) {
    return {};
  }

  const entries = {};
  const content = fs.readFileSync(filePath, "utf8");

  for (const rawLine of content.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) {
      continue;
    }

    const equalsIndex = line.indexOf("=");
    if (equalsIndex < 0) {
      continue;
    }

    const key = line.slice(0, equalsIndex).trim();
    const value = line.slice(equalsIndex + 1).trim();
    if (key) {
      entries[key] = value;
    }
  }

  return entries;
}

function resolveProvider(provider, repoUrl) {
  if (provider === "github" || provider === "bitbucket") {
    return provider;
  }

  const url = String(repoUrl || "").toLowerCase();
  if (url.includes("bitbucket")) {
    return "bitbucket";
  }

  return "github";
}

function getProviderEnv(provider) {
  const effectiveProvider = resolveProvider(provider, "");
  const envFile = providerEnvFiles[effectiveProvider];
  return {
    provider: effectiveProvider,
    envFile,
    env: parseEnvFile(envFile)
  };
}

function getProviderDefaults(provider) {
  const { provider: effectiveProvider, env } = getProviderEnv(provider);
  const localRepoPath = env.LOCAL_REPO_PATH || "";
  const resolvedLocalRepoPath = path.isAbsolute(localRepoPath)
    ? localRepoPath
    : path.resolve(repoRoot, localRepoPath);
  const generatedPath = path.join(repoRoot, "dummy_payload.txt");

  return {
    provider: effectiveProvider,
    repoUrl: env.REPO_URL || "",
    localRepoPath: resolvedLocalRepoPath,
    generatedPath,
    baseBranch: env.BASE_BRANCH || "main",
    remote: env.REMOTE || "origin",
    targetDir: env.TARGET_DIR || "tests/generated",
    commitMessage: env.COMMIT_MESSAGE || "Worktop: add generated test scripts"
  };
}

function buildChildEnv(provider, repoUrl) {
  const resolvedProvider = resolveProvider(provider, repoUrl);
  const providerEnv = parseEnvFile(providerEnvFiles[resolvedProvider]);
  const childEnv = {
    ...process.env,
    ...providerEnv,
    REPO_PROVIDER: resolvedProvider
  };

  for (const key of [
    "GIT_AUTHOR_NAME",
    "GIT_AUTHOR_EMAIL",
    "GIT_COMMITTER_NAME",
    "GIT_COMMITTER_EMAIL"
  ]) {
    if (typeof childEnv[key] === "string" && childEnv[key].trim() === "") {
      delete childEnv[key];
    }
  }

  return childEnv;
}

function validateInput(body) {
  const required = ["provider", "repoUrl", "localRepoPath", "generatedPath", "commitMessage"]; 
  for (const name of required) {
    if (!body[name] || typeof body[name] !== "string") {
      return `Missing or invalid field: ${name}`;
    }
  }

  if (!["auto", "github", "bitbucket"].includes(body.provider)) {
    return "provider must be one of: auto, github, bitbucket";
  }

  const repoUrl = body.repoUrl.trim();
  if (!repoUrl.startsWith("https://") && !repoUrl.startsWith("git@")) {
    return "repoUrl must start with https:// or git@";
  }

  const allowedPrefixes = getAllowedRepoPrefixes();
  if (allowedPrefixes.length > 0 && !allowedPrefixes.some((p) => repoUrl.startsWith(p))) {
    return "repoUrl is not in the allowed repository list";
  }

  if (!path.isAbsolute(body.localRepoPath) || !path.isAbsolute(body.generatedPath)) {
    return "localRepoPath and generatedPath must be absolute paths";
  }

  if (body.branchHint && typeof body.branchHint !== "string") {
    return "branchHint must be a string when provided";
  }

  return null;
}

function resolvePythonBin() {
  if (process.env.PYTHON_BIN) {
    return process.env.PYTHON_BIN;
  }

  if (process.platform === "win32") {
    return path.join(repoRoot, ".venv", "Scripts", "python.exe");
  }

  return "python3";
}

function runCommand({ provider, repoUrl, args }) {
  const pythonBin = resolvePythonBin();
  const scriptPath = path.join(repoRoot, "repo_rover_runner_client.py");
  const cmdArgs = [scriptPath, "--provider", provider, ...args];
  const childEnv = buildChildEnv(provider, repoUrl);

  return new Promise((resolve, reject) => {
    const child = spawn(pythonBin, cmdArgs, {
      cwd: repoRoot,
      env: childEnv,
      stdio: ["ignore", "pipe", "pipe"]
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (chunk) => {
      stdout += String(chunk);
    });

    child.stderr.on("data", (chunk) => {
      stderr += String(chunk);
    });

    child.on("error", (err) => reject(err));

    child.on("close", (code) => {
      if (code === 0) {
        resolve({ stdout, stderr, code });
        return;
      }
      reject(new Error(`Command failed (${code}): ${stderr || stdout}`));
    });
  });
}

function ensureLocalRepoPath(localRepoPath) {
  const gitDir = path.join(localRepoPath, ".git");
  return fs.existsSync(gitDir);
}

async function processJob(jobId) {
  const job = jobs.get(jobId);
  if (!job) {
    return;
  }

  job.status = "running";
  job.startedAt = new Date().toISOString();

  const {
    provider,
    repoUrl,
    localRepoPath,
    generatedPath,
    targetDir,
    baseBranch,
    remote,
    commitMessage,
    branchHint
  } = job.request;

  const safeHint = slug(branchHint || "generated-tests");
  const branch = `worktop/${safeHint}/${nowStamp()}`;

  try {
    if (!ensureLocalRepoPath(localRepoPath)) {
      const cloneResult = await runCommand({
        provider,
        args: [
          "clone",
          "--repo-url",
          repoUrl,
          "--dest",
          localRepoPath,
          "--branch",
          baseBranch
        ]
      });
      job.logs.push({ step: "clone", output: cloneResult.stdout.trim() });
    }

    const branchResult = await runCommand({
      provider,
      args: [
        "use-branch",
        "--repo-path",
        localRepoPath,
        "--branch",
        branch,
        "--base-branch",
        baseBranch,
        "--remote",
        remote
      ]
    });
    job.logs.push({ step: "use-branch", output: branchResult.stdout.trim() });

    const pushResult = await runCommand({
      provider,
      args: [
        "push-files",
        "--repo-path",
        localRepoPath,
        "--branch",
        branch,
        "--files",
        generatedPath,
        "--target-dir",
        targetDir,
        "--commit-message",
        commitMessage,
        "--base-branch",
        baseBranch,
        "--remote",
        remote
      ]
    });
    job.logs.push({ step: "push-files", output: pushResult.stdout.trim() });

    job.status = "succeeded";
    job.completedAt = new Date().toISOString();
    job.result = { branch, repoUrl };
  } catch (error) {
    job.status = "failed";
    job.completedAt = new Date().toISOString();
    job.error = String(error?.message || error);
  }
}

async function drainQueue() {
  if (processing) {
    return;
  }
  processing = true;

  while (queue.length > 0) {
    const nextJobId = queue.shift();
    await processJob(nextJobId);
  }

  processing = false;
}

app.post("/api/jobs/publish-generated-scripts", (req, res) => {
  const err = validateInput(req.body || {});
  if (err) {
    res.status(400).json({ error: err });
    return;
  }

  const request = {
    provider: req.body.provider,
    repoUrl: req.body.repoUrl,
    localRepoPath: req.body.localRepoPath,
    generatedPath: req.body.generatedPath,
    targetDir: req.body.targetDir || "tests/generated",
    baseBranch: req.body.baseBranch || "main",
    remote: req.body.remote || "origin",
    commitMessage: req.body.commitMessage,
    branchHint: req.body.branchHint || "qe-script-drop"
  };

  const jobId = randomUUID();
  jobs.set(jobId, {
    id: jobId,
    status: "queued",
    createdAt: new Date().toISOString(),
    request,
    logs: []
  });

  queue.push(jobId);
  void drainQueue();

  res.status(202).json({ jobId, status: "queued" });
});

app.get("/api/provider-config", (req, res) => {
  const provider = req.query.provider;
  if (provider !== "github" && provider !== "bitbucket") {
    res.status(400).json({ error: "provider must be github or bitbucket" });
    return;
  }

  res.json(getProviderDefaults(provider));
});

app.get("/api/jobs/:jobId", (req, res) => {
  const job = jobs.get(req.params.jobId);
  if (!job) {
    res.status(404).json({ error: "Job not found" });
    return;
  }
  res.json(job);
});

app.get("/api/health", (_req, res) => {
  res.json({ status: "ok", queued: queue.length, jobs: jobs.size });
});

app.listen(port, () => {
  console.log(`Worktop sample backend listening on http://localhost:${port}`);
});
