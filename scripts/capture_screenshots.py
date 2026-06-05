#!/usr/bin/env python3
"""Capture dashboard preview PNGs for GitHub and PyPI README.

Usage:
    pip install playwright
    playwright install chromium
    python scripts/capture_screenshots.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "screenshots"


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SystemExit(
            "Install playwright first:\n"
            "  pip install playwright\n"
            "  playwright install chromium\n"
            "  python scripts/capture_screenshots.py"
        ) from exc

    OUT.mkdir(parents=True, exist_ok=True)
    shots = [
        ("preview-dashboard.html", "dashboard.png"),
        ("preview-user-list.html", "user-list.png"),
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(device_scale_factor=2, viewport={"width": 1280, "height": 900})
        for html_name, png_name in shots:
            html_path = OUT / html_name
            page.goto(html_path.as_uri(), wait_until="networkidle")
            page.wait_for_timeout(1000)
            root = page.locator(".screenshot-root")
            root.screenshot(path=str(OUT / png_name))
            print(f"Wrote {OUT / png_name}")
        browser.close()


if __name__ == "__main__":
    main()
