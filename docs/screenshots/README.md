# Screenshots

Preview assets for GitHub README and PyPI project page.

| File | Description |
|------|-------------|
| `dashboard.png` | Main analytics dashboard |
| `user-list.png` | User list & search |
| `preview-dashboard.html` | Standalone HTML mock (source for dashboard screenshot) |
| `preview-user-list.html` | Standalone HTML mock (source for user list screenshot) |

## Regenerate PNGs

After editing the HTML previews or when the UI changes:

```bash
pip install playwright
playwright install chromium
python scripts/capture_screenshots.py
git add docs/screenshots/*.png README.md
git commit -m "Update dashboard screenshots"
git push origin main
```

## PyPI

README uses absolute URLs:

```
https://raw.githubusercontent.com/nkscoder/ai-user-activity-monitor/main/docs/screenshots/dashboard.png
```

Push screenshots to GitHub **before** uploading a new PyPI release so images appear on the PyPI project page.

## Replace with real app screenshots (optional)

1. Run your Django project with the activity dashboard open.
2. Take browser screenshots (1440px wide recommended).
3. Save as `dashboard.png` and `user-list.png` in this folder.
4. Commit and push.
