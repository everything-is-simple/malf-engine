import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CHART = ROOT / "RB-FX-007-chart-comparison"

def port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]

def test_chart_candidates_render_without_external_requests():
    p = port()
    process = subprocess.Popen([sys.executable, "-m", "http.server", str(p), "--bind", "127.0.0.1"], cwd=CHART, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(.3)
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            for page_name, selector in (("echarts.html", "canvas"), ("lightweight.html", "canvas"), ("native.html", "svg")):
                page = browser.new_page(viewport={"width": 800, "height": 400})
                external = []
                page.on("request", lambda req: external.append(req.url) if not req.url.startswith(f"http://127.0.0.1:{p}") else None)
                response = page.goto(f"http://127.0.0.1:{p}/{page_name}", wait_until="networkidle")
                assert response and response.ok
                assert page.locator(selector).count() >= 1
                assert external == []
                page.close()
            browser.close()
    finally:
        process.terminate()
        process.wait(timeout=10)
