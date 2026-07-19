from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

BASE = Path(__file__).resolve().parent
PUBLISHED = Path(os.environ.get("RISK_BENCH_FACTORY_PUBLISHED", BASE / "published")).resolve()
STATIC = BASE / "static"

app = FastAPI(
    title="RiskBench Factory Read-only Viewer",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=503, detail="published_snapshot_unavailable") from exc


def _snapshot_path(snapshot_id: str) -> Path:
    if not snapshot_id or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in snapshot_id):
        raise HTTPException(status_code=404, detail="snapshot_not_found")
    target = (PUBLISHED / snapshot_id / "snapshot.json").resolve()
    if PUBLISHED not in target.parents:
        raise HTTPException(status_code=404, detail="snapshot_not_found")
    return target


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/current")
def current():
    pointer = _read_json(PUBLISHED / "current.json")
    snapshot_id = pointer.get("snapshot_id")
    if not isinstance(snapshot_id, str):
        raise HTTPException(status_code=503, detail="published_snapshot_unavailable")
    return _read_json(_snapshot_path(snapshot_id))


@app.get("/api/snapshots/{snapshot_id}")
def snapshot(snapshot_id: str):
    return _read_json(_snapshot_path(snapshot_id))


@app.get("/healthz")
def healthz():
    return {"status": "ok", "mode": "readonly"}
