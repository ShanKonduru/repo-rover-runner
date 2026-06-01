import React from "react";
import { useEffect, useMemo, useState } from "react";

const initialForm = {
  provider: "github",
  repoUrl: "",
  localRepoPath: "",
  generatedPath: "",
  targetDir: "tests/generated",
  baseBranch: "main",
  remote: "origin",
  branchHint: "qe-script-drop",
  commitMessage: "Worktop: add generated test scripts"
};

const API_BASE = "http://localhost:4070";

export function App() {
  const [form, setForm] = useState(initialForm);
  const [jobId, setJobId] = useState("");
  const [jobState, setJobState] = useState(null);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const isTerminal = useMemo(() => {
    return jobState?.status === "succeeded" || jobState?.status === "failed";
  }, [jobState]);

  useEffect(() => {
    let cancelled = false;

    async function loadProviderDefaults() {
      try {
        const response = await fetch(`${API_BASE}/api/provider-config?provider=${form.provider}`);
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "Unable to load provider configuration");
        }

        if (!cancelled) {
          setForm((current) => ({
            ...current,
            repoUrl: data.repoUrl || current.repoUrl,
            localRepoPath: data.localRepoPath || current.localRepoPath,
            generatedPath: data.generatedPath || current.generatedPath,
            targetDir: data.targetDir || current.targetDir,
            baseBranch: data.baseBranch || current.baseBranch,
            remote: data.remote || current.remote,
            commitMessage: data.commitMessage || current.commitMessage
          }));
        }
      } catch (err) {
        if (!cancelled) {
          setError(String(err?.message || err));
        }
      }
    }

    void loadProviderDefaults();

    return () => {
      cancelled = true;
    };
  }, [form.provider]);

  async function submit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      const response = await fetch(`${API_BASE}/api/jobs/publish-generated-scripts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form)
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Failed to create publish job");
      }

      setJobId(data.jobId);
      setJobState({ status: data.status });
    } catch (err) {
      setError(String(err?.message || err));
    } finally {
      setSubmitting(false);
    }
  }

  async function refreshStatus() {
    if (!jobId) {
      return;
    }
    setError("");

    try {
      const response = await fetch(`${API_BASE}/api/jobs/${jobId}`);
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Unable to fetch job state");
      }
      setJobState(data);
    } catch (err) {
      setError(String(err?.message || err));
    }
  }

  return (
    <main className="shell">
      <section className="panel">
        <h1>Worktop Integration Sample</h1>
        <p>
          This sample pushes AI-generated scripts to GitHub/Bitbucket by calling the existing Python workspace code from a Node backend.
        </p>

        <form onSubmit={submit} className="grid">
          <label>
            Provider
            <select
              value={form.provider}
              onChange={(e) => setForm({ ...form, provider: e.target.value })}
            >
              <option value="github">github</option>
              <option value="bitbucket">bitbucket</option>
            </select>
          </label>

          <label>
            Repo URL
            <input
              value={form.repoUrl}
              onChange={(e) => setForm({ ...form, repoUrl: e.target.value })}
              placeholder="https://github.com/your-org/your-repo.git"
              required
            />
          </label>

          <label>
            Local Repo Path (absolute)
            <input
              value={form.localRepoPath}
              onChange={(e) => setForm({ ...form, localRepoPath: e.target.value })}
              placeholder="C:/worktop/repos/your-repo"
              required
            />
          </label>

          <label>
            Generated Script File Path (absolute)
            <input
              value={form.generatedPath}
              onChange={(e) => setForm({ ...form, generatedPath: e.target.value })}
              placeholder="C:/MyProjects/repo-rover-runner/dummy_payload.txt"
              required
            />
          </label>

          <label>
            Target Dir in Repo
            <input
              value={form.targetDir}
              onChange={(e) => setForm({ ...form, targetDir: e.target.value })}
            />
          </label>

          <label>
            Base Branch
            <input
              value={form.baseBranch}
              onChange={(e) => setForm({ ...form, baseBranch: e.target.value })}
            />
          </label>

          <label>
            Remote
            <input
              value={form.remote}
              onChange={(e) => setForm({ ...form, remote: e.target.value })}
            />
          </label>

          <label>
            Branch Hint
            <input
              value={form.branchHint}
              onChange={(e) => setForm({ ...form, branchHint: e.target.value })}
              placeholder="ticket-or-scenario"
            />
          </label>

          <label>
            Commit Message
            <input
              value={form.commitMessage}
              onChange={(e) => setForm({ ...form, commitMessage: e.target.value })}
              required
            />
          </label>

          <div className="actions">
            <button type="submit" disabled={submitting}>
              {submitting ? "Submitting..." : "Publish Generated Scripts"}
            </button>
            <button type="button" disabled={!jobId} onClick={refreshStatus}>
              Refresh Status
            </button>
          </div>
        </form>

        {jobId && <p className="meta">Job ID: {jobId}</p>}
        {jobState?.status && <p className="meta">Current Status: {jobState.status}</p>}
        {jobState?.result?.branch && (
          <p className="meta">Published Branch: {jobState.result.branch}</p>
        )}
        {jobState?.error && <p className="error">{jobState.error}</p>}
        {error && <p className="error">{error}</p>}

        {jobState?.logs?.length > 0 && (
          <section className="logs">
            <h2>Execution Logs</h2>
            {jobState.logs.map((entry, index) => (
              <pre key={`${entry.step}-${index}`}>
{`[${entry.step}]\n${entry.output}`}
              </pre>
            ))}
          </section>
        )}

        {isTerminal && (
          <p className="hint">
            This sample demonstrates queueing, provider selection, branch policy, and Python CLI orchestration from React through Node.
          </p>
        )}
      </section>
    </main>
  );
}
