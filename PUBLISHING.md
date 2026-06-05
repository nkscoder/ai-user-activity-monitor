# Publishing to PyPI — ai-user-activity-monitor

PyPI package: **`ai-user-activity-monitor`**  
Django app import: **`activity`**

---

## 1. One-time PyPI setup

1. Create accounts:
   - [PyPI](https://pypi.org/account/register/)
   - [TestPyPI](https://test.pypi.org/account/register/) (recommended for first upload)
2. Enable **2FA** on PyPI.
3. Create an **API token**:
   - PyPI → Account settings → API tokens → “Add API token”
   - Scope: entire account (first publish) or project `ai-user-activity-monitor`
   - Save token (starts with `pypi-`)

---

## 2. Build locally

```bash
cd /path/to/ai-user-activity-monitor
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip build twine
python -m build
```

This creates `dist/ai_user_activity_monitor-1.0.0.tar.gz` and `.whl`.

Verify the wheel contains templates and migrations:

```bash
unzip -l dist/*.whl | grep -E 'templates|migrations'
```

---

## 3. Upload to TestPyPI (recommended first)

```bash
twine upload --repository testpypi dist/*
```

Username: `__token__`  
Password: your TestPyPI API token

Test install:

```bash
pip install --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  ai-user-activity-monitor
```

---

## 4. Upload to PyPI (production)

```bash
twine upload dist/*
```

After publish, users install with:

```bash
pip install ai-user-activity-monitor
```

---

## 5. Screenshots (GitHub + PyPI)

README images must be on GitHub `main` **before** PyPI upload (PyPI loads them from raw GitHub URLs).

```bash
python scripts/capture_screenshots.py   # or replace PNGs manually
git add docs/screenshots/*.png README.md
git push origin main
```

Then build and upload. PyPI page: [pypi.org/project/ai-user-activity-monitor](https://pypi.org/project/ai-user-activity-monitor)

---

## 6. Version bumps

Before each release:

1. Bump `version` in `pyproject.toml`
2. Bump `PACKAGE_VERSION` in `conf.py` (optional, for footer display)
3. Commit, tag, push:

```bash
git add pyproject.toml conf.py
git commit -m "Release v1.0.1"
git tag v1.0.1
git push origin main --tags
python -m build
twine upload dist/*
```

---

## 7. GitHub Actions (optional)

See `.github/workflows/publish-pypi.yml`. Add repository secrets:

| Secret | Value |
|--------|--------|
| `PYPI_API_TOKEN` | PyPI API token |

Create a GitHub **Release** with tag `v1.0.0` to trigger automatic upload.

---

## Install in Django (after PyPI publish)

```bash
pip install ai-user-activity-monitor
```

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "activity.apps.ActivityConfig",
]
```

```python
# urls.py
path("user/activity/", include("activity.urls")),
```

```bash
python manage.py migrate activity
```
