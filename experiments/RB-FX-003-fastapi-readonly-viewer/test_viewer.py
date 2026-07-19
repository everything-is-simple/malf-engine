import hashlib
from pathlib import Path

from fastapi.testclient import TestClient

from app import PUBLISHED, app

client = TestClient(app)


def digest_tree(root: Path):
    return {str(p.relative_to(root)): (p.stat().st_mtime_ns, hashlib.sha256(p.read_bytes()).hexdigest()) for p in root.rglob("*") if p.is_file()}


def test_read_routes_and_docs_disabled():
    assert client.get("/").status_code == 200
    response = client.get("/api/current")
    assert response.status_code == 200
    assert response.json()["usage_level"] == "research_only"
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_all_write_methods_are_rejected_and_files_unchanged():
    before = digest_tree(PUBLISHED)
    for method in ("post", "put", "patch", "delete"):
        assert client.request(method.upper(), "/api/current", json={"x": 1}).status_code == 405
    assert client.get("/api/current").status_code == 200
    assert digest_tree(PUBLISHED) == before


def test_missing_current_fails_without_scanning_old_snapshot(tmp_path, monkeypatch):
    import app as module
    broken = tmp_path / "published"
    (broken / "old-snapshot").mkdir(parents=True)
    (broken / "old-snapshot" / "snapshot.json").write_text('{"snapshot_id":"old-snapshot"}', encoding="utf-8")
    monkeypatch.setattr(module, "PUBLISHED", broken)
    assert client.get("/api/current").status_code == 503


def test_absolute_paths_are_not_exposed():
    body = client.get("/api/current").text
    assert "J:\\" not in body
    assert "vipdoc" not in body

