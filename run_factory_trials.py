from __future__ import annotations

import hashlib
import importlib.metadata as md
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = ROOT / ".venv" / "Scripts" / "python.exe"
UV = ROOT / ".venv" / "Scripts" / "uv.exe"
ENV = dict(os.environ)
NODE = shutil.which("node") or "node.exe"
NPM = shutil.which("npm.cmd") or shutil.which("npm") or "npm.cmd"
GIT = shutil.which("git") or "git.exe"

ENV["PYTHONPATH"] = os.pathsep.join(str(ROOT / "experiments" / name) for name in (
    "RB-FX-001-python-boundary",
    "RB-FX-002-pydantic-contract",
    "RB-FX-003-fastapi-readonly-viewer",
))


def run(command: list[str], cwd: Path = ROOT) -> dict:
    completed = subprocess.run(command, cwd=cwd, env=ENV, text=True, capture_output=True)
    return {
        "command": subprocess.list2cmdline(command),
        "cwd": str(cwd),
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_result(exp_id: str, result: dict) -> None:
    target = ROOT / "evidence" / exp_id
    target.mkdir(parents=True, exist_ok=True)
    result["recorded_at_utc"] = datetime.now(timezone.utc).isoformat()
    result["environment"] = {
        "os": platform.platform(),
        "python": platform.python_version(),
        "node": run([NODE, "--version"])["stdout"].strip(),
        "npm": run([NPM, "--version"])["stdout"].strip(),
        "git": run([GIT, "--version"])["stdout"].strip(),
    }
    (target / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


packages = {name: md.version(name) for name in ("fastapi", "uvicorn", "pydantic", "pytest", "httpx", "playwright", "pytest-playwright", "uv")}

fx1 = run([str(PY), "-m", "pytest", "-q", "experiments/RB-FX-001-python-boundary"])
write_result("RB-FX-001-python-boundary", {
    "status": "trial-passed" if fx1["exit_code"] == 0 else "rejected",
    "component": "Python 3.10 standard library",
    "license": "PSF License",
    "test": fx1,
    "artifacts_sha256": {
        "boundary.py": digest(ROOT / "experiments/RB-FX-001-python-boundary/boundary.py"),
        "test_boundary.py": digest(ROOT / "experiments/RB-FX-001-python-boundary/test_boundary.py"),
    },
    "limitations": ["synthetic fixture only", "not a production TDX parser"],
    "assembly_recommendation": "Use standard library primitives as the main Data/Core foundation; port only through an approved task plan, not by copying this trial file.",
})

fx2 = run([str(PY), "-m", "pytest", "-q", "experiments/RB-FX-002-pydantic-contract"])
write_result("RB-FX-002-pydantic-contract", {
    "status": "trial-passed" if fx2["exit_code"] == 0 else "rejected",
    "component": "Pydantic v2 boundary contracts",
    "version": packages["pydantic"],
    "license": "MIT",
    "test": fx2,
    "limitations": ["boundary validation only", "must not encode MALF domain semantics"],
    "assembly_recommendation": "Recommend for config/snapshot/lineage boundary validation only.",
})

fx3 = run([str(PY), "-m", "pytest", "-q", "experiments/RB-FX-003-fastapi-readonly-viewer"])
write_result("RB-FX-003-fastapi-readonly-viewer", {
    "status": "trial-passed" if fx3["exit_code"] == 0 else "rejected",
    "components": {"fastapi": packages["fastapi"], "uvicorn": packages["uvicorn"], "httpx": packages["httpx"]},
    "licenses": {"fastapi": "MIT", "uvicorn": "BSD-3-Clause", "httpx": "BSD-3-Clause"},
    "test": fx3,
    "limitations": ["FastAPI/Starlette TestClient emitted a deprecation warning for the HTTP client integration", "factory fixture is not production snapshot schema", "binding is a deployment command responsibility"],
    "assembly_recommendation": "Recommend FastAPI+Uvicorn for the GET/HEAD-only Viewer boundary, with production tests favoring live Uvicorn/HTTP or resolving the TestClient deprecation before lock-in.",
})

failure_file = ROOT / "evidence" / "RB-FX-004-pytest-harness" / "intentional_failure_tmp.py"
failure_file.parent.mkdir(parents=True, exist_ok=True)
failure_file.write_text("def test_intentional_failure():\n    assert False\n", encoding="utf-8")
try:
    fx4_failure = run([str(PY), "-m", "pytest", "-q", str(failure_file)])
finally:
    failure_file.unlink(missing_ok=True)
write_result("RB-FX-004-pytest-harness", {
    "status": "trial-passed" if fx4_failure["exit_code"] != 0 else "rejected",
    "component": "pytest",
    "version": packages["pytest"],
    "license": "MIT",
    "intentional_failure_probe": fx4_failure,
    "limitations": ["coverage and reporting plugins are not yet selected"],
    "assembly_recommendation": "Recommend pytest as the TDD runner; add plugins only when a task proves the need.",
})

fx5 = run([str(PY), "-m", "pytest", "-q", "experiments/RB-FX-005-playwright-viewer"])
write_result("RB-FX-005-playwright-viewer", {
    "status": "trial-passed" if fx5["exit_code"] == 0 else "rejected",
    "components": {"playwright": packages["playwright"], "pytest-playwright": packages["pytest-playwright"]},
    "licenses": {"playwright": "Apache-2.0", "pytest-playwright": "Apache-2.0"},
    "test": fx5,
    "limitations": ["Chromium browser payload is large", "development/acceptance dependency only", "browser cache location is external to the repository unless PLAYWRIGHT_BROWSERS_PATH is explicitly controlled"],
    "assembly_recommendation": "Recommend only for Viewer acceptance tests, never as a production runtime dependency.",
})

uv_project = ROOT / "experiments/RB-FX-006-package-manager"
uv_probe = run([str(UV), "sync", "--project", str(uv_project)], cwd=ROOT)
uv_run = run([str(UV), "run", "--project", str(uv_project), "python", "--version"], cwd=ROOT)
write_result("RB-FX-006-package-manager", {
    "status": "trial-passed" if uv_probe["exit_code"] == 0 and uv_run["exit_code"] == 0 else "rejected",
    "candidates": {"venv-pip": {"python": platform.python_version(), "pip": md.version("pip")}, "uv": packages["uv"]},
    "license": {"venv-pip": "PSF/MIT", "uv": "MIT OR Apache-2.0"},
    "uv_sync": uv_probe,
    "uv_runtime_probe": uv_run,
    "lock_sha256": digest(uv_project / "uv.lock"),
    "limitations": ["uv reported hardlink fallback to copy because cache and target are on different filesystems", "uv must remain a development tool and not a Viewer runtime dependency", "offline rebuild on the target small host remains a future deployment acceptance item"],
    "assembly_recommendation": "Recommend uv as the preferred development resolver/lock tool with venv/pip as the lowest-common-denominator fallback; do not require uv to start the Viewer.",
})

chart_dir = ROOT / "experiments/RB-FX-007-chart-comparison"
chart_probe = run([NODE, "smoke.mjs"], cwd=chart_dir)
chart_render = run([str(PY), "-m", "pytest", "-q", "experiments/RB-FX-005-playwright-viewer/test_charts.py"])
chart_data = json.loads(chart_probe["stdout"]) if chart_probe["exit_code"] == 0 else []
write_result("RB-FX-007-chart-comparison", {
    "status": "trial-passed" if chart_probe["exit_code"] == 0 and chart_render["exit_code"] == 0 else "rejected",
    "candidates": chart_data,
    "package_lock_sha256": digest(chart_dir / "package-lock.json"),
    "metadata_probe": chart_probe,
    "render_probe": chart_render,
    "limitations": ["rendering success does not prove a v0.1 need for a chart dependency", "accessibility and exact financial semantics require task-specific acceptance", "ECharts bundle is materially larger than Lightweight Charts, while native SVG adds no third-party runtime"],
    "assembly_recommendation": "Select native HTML/CSS/SVG as the v0.1 default. Defer ECharts and Lightweight Charts until a concrete chart task proves the need; if candlestick interaction is required, trial Lightweight Charts first because of its smaller tested browser bundle.",
})

summary = {
    "status": "complete",
    "packages": packages,
    "results": {p.parent.name: json.loads(p.read_text(encoding="utf-8"))["status"] for p in sorted((ROOT / "evidence").glob("*/result.json"))},
}
(ROOT / "evidence" / "SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))

