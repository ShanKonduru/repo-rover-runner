#!/usr/bin/env python3
"""Generate JSON and HTML security reports under test_results/Secutiry_reports."""

from __future__ import annotations

import datetime as dt
import html
import json
import shutil
import subprocess  # nosec B404
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "test_results" / "Secutiry_reports"


class ToolRunResult:
    def __init__(self, name: str, command: List[str], returncode: int, stdout: str, stderr: str, json_path: Path) -> None:
        self.name = name
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.json_path = json_path


def run_command(command: List[str], cwd: Path, timeout_seconds: int = 120) -> Tuple[int, str, str]:
    try:
        process = subprocess.run(  # nosec B603
            command,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout_seconds,
        )
        return process.returncode, process.stdout, process.stderr
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        stderr = (stderr + "\n" if stderr else "") + f"Command timed out after {timeout_seconds}s"
        return 124, stdout, stderr


def run_pip_audit(json_path: Path) -> ToolRunResult:
    cmd = [sys.executable, "-m", "pip_audit", "-f", "json", "-o", str(json_path)]
    rc, out, err = run_command(cmd, ROOT)
    return ToolRunResult("pip-audit", cmd, rc, out, err, json_path)


def run_bandit(json_path: Path) -> ToolRunResult:
    cmd = [
        sys.executable,
        "-m",
        "bandit",
        "-r",
        "repo_rover_runner",
        "repo_rover_runner_client.py",
        "repo_rover_runner_cli.py",
        "repo_rover_runner_mcp_server.py",
        "-x",
        "tests,tmp",
        "-f",
        "json",
        "-o",
        str(json_path),
    ]
    rc, out, err = run_command(cmd, ROOT)
    return ToolRunResult("bandit", cmd, rc, out, err, json_path)


def run_gitleaks(json_path: Path) -> ToolRunResult:
    gitleaks = shutil.which("gitleaks")
    if gitleaks:
        cmd = [
            gitleaks,
            "detect",
            "--source",
            ".",
            "--report-format",
            "json",
            "--report-path",
            str(json_path),
            "--exit-code",
            "0",
            "--no-banner",
        ]
        rc, out, err = run_command(cmd, ROOT)
        return ToolRunResult("gitleaks", cmd, rc, out, err, json_path)

    fallback_cmd = [sys.executable, "-m", "gitleaks", "detect", "--source", ".", "--report-format", "json", "--report-path", str(json_path)]
    rc, out, err = run_command(fallback_cmd, ROOT)
    return ToolRunResult("gitleaks", fallback_cmd, rc, out, err, json_path)


def _render_json_html(title: str, json_data: Any) -> str:
    pretty = html.escape(json.dumps(json_data, indent=2, ensure_ascii=False))
    return (
        "<!doctype html>\n"
        "<html lang=\"en\">\n"
        "<head><meta charset=\"utf-8\"><title>"
        + html.escape(title)
        + "</title>"
        "<style>body{font-family:Segoe UI,Tahoma,sans-serif;margin:24px;background:#f7f9fc;color:#0f172a;}"
        "h1{margin:0 0 12px;}pre{white-space:pre-wrap;background:#0b1020;color:#d6e1ff;padding:16px;border-radius:10px;overflow:auto;}"
        "</style></head><body><h1>"
        + html.escape(title)
        + "</h1><pre>"
        + pretty
        + "</pre></body></html>"
    )


def convert_json_to_html_with_sec_report_kit(tool_name: str, json_path: Path, html_path: Path) -> bool:
    tool = shutil.which("sec-report-kit")
    if not tool:
        return False

    tool_map = {
        "pip-audit": "pip-audit",
        "bandit": "bandit",
        "gitleaks": "gitleaks",
    }
    subcommand = tool_map.get(tool_name, "auto")

    commands = [
        [tool, "render", subcommand, "--input", str(json_path), "--output", str(html_path)],
        [tool, "render", "auto", "--input", str(json_path), "--output", str(html_path)],
    ]

    for cmd in commands:
        rc, _out, _err = run_command(cmd, ROOT)
        if rc == 0 and html_path.exists() and html_path.stat().st_size > 0:
            return True

    return False


def ensure_tool_html_report(tool_name: str, json_path: Path, html_path: Path) -> bool:
    if convert_json_to_html_with_sec_report_kit(tool_name, json_path, html_path):
        return True

    try:
        parsed = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception:
        parsed = {"error": f"Unable to parse JSON report: {json_path.name}"}

    html_path.write_text(_render_json_html(f"{tool_name} security report", parsed), encoding="utf-8")
    return False


def summarize_result(tool_name: str, data: Any) -> str:
    if tool_name == "pip-audit":
        deps = data.get("dependencies", []) if isinstance(data, dict) else []
        vulns = 0
        for dep in deps:
            vulns += len(dep.get("vulns", []))
        return f"dependencies={len(deps)}, vulnerabilities={vulns}"

    if tool_name == "bandit":
        results = data.get("results", []) if isinstance(data, dict) else []
        high = 0
        medium = 0
        low = 0
        for item in results:
            sev = str(item.get("issue_severity", "")).upper()
            if sev == "HIGH":
                high += 1
            elif sev == "MEDIUM":
                medium += 1
            elif sev == "LOW":
                low += 1
        return f"issues={len(results)}, high={high}, medium={medium}, low={low}"

    if tool_name == "gitleaks":
        findings = data if isinstance(data, list) else data.get("findings", []) if isinstance(data, dict) else []
        return f"findings={len(findings)}"

    return "summary unavailable"


def build_consolidated_html_with_sec_report_kit() -> bool:
    tool = shutil.which("sec-report-kit")
    if not tool:
        return False

    desired_output = REPORT_DIR / "security_consolidated.html"
    known_tool_html = {
        REPORT_DIR / "pip_audit_report.html",
        REPORT_DIR / "bandit_report.html",
        REPORT_DIR / "gitleaks_report.html",
        desired_output,
    }

    before = {path: path.stat().st_mtime for path in REPORT_DIR.glob("*.html")}
    cmd = [tool, "render", "consolidated", "--input", str(REPORT_DIR), "--output", str(REPORT_DIR), "--target", "repo-rover-runner"]
    rc, _out, _err = run_command(cmd, ROOT)
    if rc != 0:
        return False

    if desired_output.exists() and desired_output.stat().st_size > 0:
        return True

    candidates: List[Path] = []
    for path in REPORT_DIR.glob("*.html"):
        if path in known_tool_html:
            continue
        old_mtime = before.get(path)
        if old_mtime is None or path.stat().st_mtime >= old_mtime:
            candidates.append(path)

    if not candidates:
        return False

    source = max(candidates, key=lambda item: item.stat().st_mtime)
    desired_output.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return desired_output.exists() and desired_output.stat().st_size > 0


def build_consolidated_html(results: List[ToolRunResult], generated_html: Dict[str, Path]) -> Path:
    consolidated_path = REPORT_DIR / "security_consolidated.html"
    rows: List[str] = []

    for result in results:
        tool_json = result.json_path
        tool_html = generated_html[result.name]
        parsed: Any = {}
        summary = "summary unavailable"

        if tool_json.exists():
            try:
                parsed = json.loads(tool_json.read_text(encoding="utf-8"))
                summary = summarize_result(result.name, parsed)
            except Exception:
                summary = "unable to parse JSON"

        rows.append(
            "<tr>"
            f"<td>{html.escape(result.name)}</td>"
            f"<td>{result.returncode}</td>"
            f"<td>{html.escape(summary)}</td>"
            f"<td><a href=\"{html.escape(tool_json.name)}\">{html.escape(tool_json.name)}</a></td>"
            f"<td><a href=\"{html.escape(tool_html.name)}\">{html.escape(tool_html.name)}</a></td>"
            "</tr>"
        )

    now = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d %H:%M:%SZ")
    page = (
        "<!doctype html>\n"
        "<html lang=\"en\">\n"
        "<head><meta charset=\"utf-8\"><title>Security Reports</title>"
        "<style>body{font-family:Segoe UI,Tahoma,sans-serif;margin:24px;background:#f6f8fb;color:#0f172a;}"
        "h1{margin:0 0 8px;}"
        "table{border-collapse:collapse;width:100%;background:#fff;border-radius:10px;overflow:hidden;}"
        "th,td{border:1px solid #d8dee9;padding:10px;text-align:left;vertical-align:top;}"
        "th{background:#eef2f8;}"
        "a{color:#0b5fff;text-decoration:none;}a:hover{text-decoration:underline;}"
        "</style></head><body>"
        "<h1>Consolidated Security Report</h1>"
        f"<p>Generated at {html.escape(now)} from repo-rover-runner scans.</p>"
        "<table><thead><tr><th>Tool</th><th>Exit Code</th><th>Summary</th><th>JSON</th><th>HTML</th></tr></thead>"
        "<tbody>"
        + "".join(rows)
        + "</tbody></table></body></html>"
    )
    consolidated_path.write_text(page, encoding="utf-8")
    return consolidated_path


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    results = [
        run_pip_audit(REPORT_DIR / "pip_audit_report.json"),
        run_bandit(REPORT_DIR / "bandit_report.json"),
        run_gitleaks(REPORT_DIR / "gitleaks_report.json"),
    ]

    generated_html: Dict[str, Path] = {}
    generated_with_sec_report_kit: Dict[str, bool] = {}
    for result in results:
        html_path = REPORT_DIR / f"{result.name.replace('-', '_')}_report.html"
        used_sec_report_kit = ensure_tool_html_report(result.name, result.json_path, html_path)
        generated_html[result.name] = html_path
        generated_with_sec_report_kit[result.name] = used_sec_report_kit

    if build_consolidated_html_with_sec_report_kit():
        consolidated = REPORT_DIR / "security_consolidated.html"
        consolidated_renderer = "sec-report-kit"
    else:
        consolidated = build_consolidated_html(results, generated_html)
        consolidated_renderer = "built-in-fallback"

    print(f"Security reports generated in: {REPORT_DIR}")
    for result in results:
        renderer = "sec-report-kit" if generated_with_sec_report_kit[result.name] else "built-in-fallback"
        print(
            f"- {result.name}: json={result.json_path.name} "
            f"html={generated_html[result.name].name} rc={result.returncode} renderer={renderer}"
        )
    print(f"- consolidated: {consolidated.name} renderer={consolidated_renderer}")

    # Do not fail the entire report generation pipeline for scanner findings.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
