"""Capture README screenshots from a running instance.

Usage:
    pip install playwright && playwright install --with-deps chromium
    python scripts/screenshots.py https://your-app.example.com docs/screenshots
"""

import sys
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright


def main(base_url: str, out_dir: str) -> None:
    base_url = base_url.rstrip("/")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Start from clean demo data so screenshots are reproducible.
    req = urllib.request.Request(f"{base_url}/api/demo/reset", method="POST")
    urllib.request.urlopen(req, timeout=30)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
        page.goto(base_url, wait_until="networkidle")
        page.wait_for_timeout(2000)
        page.screenshot(path=out / "1-dashboard.png")

        page.get_by_role("button", name="Optimize routes").click()
        page.wait_for_selector(".route-card", timeout=30000)
        page.wait_for_timeout(2500)
        page.screenshot(path=out / "2-optimized.png")

        page.locator(".route-card").first.click()
        page.wait_for_timeout(1500)
        page.screenshot(path=out / "3-route-detail.png")

        page.get_by_role("tab", name="Stops").click()
        page.locator(".chip", has_text="Start").first.click()
        page.wait_for_timeout(800)
        page.locator(".chip", has_text="Delivered").first.click()
        page.wait_for_timeout(1500)
        page.screenshot(path=out / "4-stops.png")

        mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=3)
        mobile.goto(base_url, wait_until="networkidle")
        mobile.wait_for_timeout(2500)
        mobile.screenshot(path=out / "5-mobile.png", full_page=True)

        api = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
        api.goto(f"{base_url}/docs", wait_until="networkidle")
        api.wait_for_timeout(1500)
        api.screenshot(path=out / "6-api-docs.png")

        browser.close()

    # Leave the live demo in its clean starting state.
    urllib.request.urlopen(
        urllib.request.Request(f"{base_url}/api/demo/reset", method="POST"), timeout=30
    )
    print("Saved:", ", ".join(sorted(f.name for f in out.glob("*.png"))))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "docs/screenshots")
