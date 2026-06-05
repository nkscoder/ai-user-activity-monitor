# ai-user-activity-monitor

**Author:** [Nitesh Kumar Singh](https://nkscoder.in) · **GitHub:** [@nkscoder](https://github.com/nkscoder)  
**Repository:** [github.com/nkscoder/ai-user-activity-monitor](https://github.com/nkscoder/ai-user-activity-monitor)

Open-source **Django user activity monitor** — page views, logins, search terms, time-on-page, and staff dashboards. Built by **Nitesh Kumar Singh** (`nkscoder`) as a reusable `activity` app for any Django project.

![AI User Activity Monitor — staff analytics dashboard](https://raw.githubusercontent.com/nkscoder/ai-user-activity-monitor/main/docs/screenshots/dashboard.png)

| | |
|---|---|
| **Maintainer** | Nitesh Kumar Singh — [nkscoder.in](https://nkscoder.in) |
| **Repo** | [ai-user-activity-monitor](https://github.com/nkscoder/ai-user-activity-monitor) |
| **PyPI** | [pypi.org/project/ai-user-activity-monitor](https://pypi.org/project/ai-user-activity-monitor) |
| **Django app** | `activity` |
| **Version** | 1.0.2 |
| **License** | [MIT](LICENSE) |

---

## Screenshots

### Analytics dashboard

Online users, login frequency, app-section visits, time-on-page charts, and a live activity feed.

![Dashboard — charts, online users, live feed](https://raw.githubusercontent.com/nkscoder/ai-user-activity-monitor/main/docs/screenshots/dashboard.png)

### User list & search

Searchable user table with pagination, last activity, login counts, and Excel export.

![User list — search, pagination, export](https://raw.githubusercontent.com/nkscoder/ai-user-activity-monitor/main/docs/screenshots/user-list.png)

> **PyPI note:** README images use absolute GitHub URLs so they render on [pypi.org/project/ai-user-activity-monitor](https://pypi.org/project/ai-user-activity-monitor).

---

## Features

- Automatic **page view** and **POST action** logging (middleware)
- **Time on page** via client-side beacon (`page-time` endpoint)
- **Search term** capture from common query params (`search`, `q`, `query`, …)
- Staff **dashboard**: online users, login frequency charts, app-section visits, live feed
- **User list** with search, pagination, Excel export
- **Per-user** activity detail and time-by-path breakdown
- **Dynamic section labels** from installed Django apps and model `verbose_name`
- Uses **`AUTH_USER_MODEL`** (no hardcoded user app)

---

## Requirements

| Package | Version |
|---------|---------|
| Python | 3.10+ |
| Django | 4.2+ |
| openpyxl | 3.1+ (Excel export) |

Uses Django **`AUTH_USER_MODEL`** everywhere. Your user model should support `is_staff` / `is_superuser` for dashboard access.

---

## Quick install

### From PyPI (recommended)

```bash
pip install ai-user-activity-monitor
```

PyPI: [pypi.org/project/ai-user-activity-monitor](https://pypi.org/project/ai-user-activity-monitor)

### From GitHub

```bash
pip install git+https://github.com/nkscoder/ai-user-activity-monitor.git
```

### Editable / local development

```bash
git clone https://github.com/nkscoder/ai-user-activity-monitor.git
cd ai-user-activity-monitor
pip install -e ".[dev]"
```

> **Note:** PyPI package name is `ai-user-activity-monitor`; Django app label is `activity`.

### `settings.py`

```python
INSTALLED_APPS = [
    # ...
    "activity.apps.ActivityConfig",
]

MIDDLEWARE = [
    # ...
    "activity.middleware.RequestIdMiddleware",
    "activity.middleware.ActivityLogMiddleware",
]

TEMPLATES[0]["OPTIONS"]["context_processors"] += [
    "activity.context_processors.activity_request_id",
    "activity.context_processors.activity_open_source",
]
```

### `urls.py`

```python
urlpatterns = [
    # ...
    path("user/activity/", include("activity.urls")),
]
```

Run migrations:

```bash
python manage.py makemigrations activity
python manage.py migrate
```

---

## Configuration (`ACTIVITY_*`)

| Setting | Default | Description |
|---------|---------|-------------|
| `ACTIVITY_GITHUB_URL` | `https://github.com/nkscoder/ai-user-activity-monitor` | Open-source repo link |
| `ACTIVITY_HOMEPAGE_URL` | `https://nkscoder.in` | Author site |
| `ACTIVITY_AUTHOR_NAME` | `Nitesh Kumar Singh` | Display name |
| `ACTIVITY_AUTHOR_HANDLE` | `nkscoder` | Handle / brand |
| `ACTIVITY_SEARCH_PLACEHOLDER` | generic search hint | User list search box |
| `ACTIVITY_PATH_LABEL_RULES` | `[]` | Optional `(regex, label)` overrides |
| `ACTIVITY_EXCLUDED_APP_LABELS` | `None` (auto) | App labels hidden from charts |
| `ACTIVITY_EXCLUDED_CHART_SECTIONS` | `()` | Extra section titles to hide |
| `ACTIVITY_USER_SEARCH_FIELDS` | `None` (auto) | Char/email fields on user model |
| `ACTIVITY_USER_EXPORT_COLUMNS` | `None` (auto) | Excel columns |
| `ACTIVITY_USER_LIST_COLUMNS` | `None` (auto) | User list table columns |
| `ACTIVITY_USER_IDENTIFIER_FIELDS` | `None` (auto) | Primary identifier fields |
| `ACTIVITY_SESSION_CONTEXT_KEYS` | `()` | Session keys passed into templates |

Section names are resolved automatically, e.g. URL `/tickets/…` → app `verbose_name`, `/tickets/ticket/…` → app + model `verbose_name_plural`.

---

## URLs

| Path | Name | Description |
|------|------|-------------|
| `dashboard/user-activity/` | `user_activity_dashboard` | Main analytics dashboard |
| `dashboard/users/` | `activity_user_list` | Searchable user list |
| `dashboard/users/<id>/` | `activity_user_detail` | Per-user logs |
| `dashboard/users/export-excel/` | `export_user_list_excel` | Excel download |
| `page-time/` | `page_time` | Duration beacon (POST) |
| `license/` | `activity_license` | MIT license page |

---

## Publish to PyPI (maintainers)

See [PUBLISHING.md](PUBLISHING.md) for build, TestPyPI, and production upload steps.

---

## About Nitesh Kumar Singh (nkscoder)

**Nitesh Kumar Singh** develops reusable Django packages under **nkscoder**. **ai-user-activity-monitor** is published on GitHub for teams who need user activity analytics without vendor lock-in.

- Website: [nkscoder.in](https://nkscoder.in)
- GitHub: [github.com/nkscoder](https://github.com/nkscoder)
- Repo: [ai-user-activity-monitor](https://github.com/nkscoder/ai-user-activity-monitor)

---

## License

Copyright © 2026 **Nitesh Kumar Singh** ([nkscoder](https://github.com/nkscoder)).

Released under the [MIT License](LICENSE).
