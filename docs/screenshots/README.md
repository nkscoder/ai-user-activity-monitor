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

README uses jsDelivr (reliable on PyPI):

```
https://cdn.jsdelivr.net/gh/nkscoder/ai-user-activity-monitor@v1.0.5/docs/screenshots/dashboard.png
```

Update `@v1.0.5` to the new release tag in `README.md` before each PyPI upload.

## Replace with real app screenshots (optional)

1. Run your Django project with the activity dashboard open.
2. Take browser screenshots (1440px wide recommended).
3. Save as `dashboard.png` and `user-list.png` in this folder.
4. Commit and push.
