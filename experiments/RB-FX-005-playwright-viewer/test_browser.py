from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
VIEWER = ROOT / "RB-FX-003-fastapi-readonly-viewer"


def _free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="module")
def viewer_url():
    port = _free_port()
    env = dict(os.environ)
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
        cwd=VIEWER,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    url = f"http://127.0.0.1:{port}"
    for _ in range(60):
        try:
            import urllib.request
            with urllib.request.urlopen(url + "/healthz", timeout=.2) as response:
                if response.status == 200:
                    break
        except Exception:
            time.sleep(.1)
    else:
        process.terminate()
        raise RuntimeError("viewer did not start")
    yield url
    process.terminate()
    process.wait(timeout=10)


@pytest.mark.parametrize("viewport", [{"width": 390, "height": 844}, {"width": 820, "height": 1180}, {"width": 1440, "height": 900}])
def test_three_viewports_are_readonly_and_offline(viewer_url, viewport):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=viewport)
        external = []
        page.on("request", lambda req: external.append(req.url) if not req.url.startswith(viewer_url) else None)
        response = page.goto(viewer_url, wait_until="networkidle")
        assert response and response.ok
        text = page.locator("body").inner_text()
        for required in ("research_only", "raw_none", "评估日", "数据截止", "None", "range_not_implemented", "审计详情"):
            assert required in text
        page.reload(wait_until="networkidle")
        assert external == []
        browser.close()
