"""Configurable settings for ai-user-activity-monitor (open source by nkscoder).

Author: Nitesh Kumar Singh — https://github.com/nkscoder
"""

from django.conf import settings


DEFAULTS = {
    "BASE_TEMPLATE": "base.html",
    "LOGIN_URL": "login",
    "GITHUB_URL": "https://github.com/nkscoder/ai-user-activity-monitor",
    "HOMEPAGE_URL": "https://nkscoder.in",
    "AUTHOR_NAME": "Nitesh Kumar Singh",
    "AUTHOR_HANDLE": "nkscoder",
    "PACKAGE_NAME": "ai-user-activity-monitor",
    "PACKAGE_VERSION": "1.0.2",
    "SEO_SITE_NAME": "AI User Activity Monitor",
    "SEO_DESCRIPTION": (
        "ai-user-activity-monitor — open-source Django user activity tracking by "
        "Nitesh Kumar Singh (nkscoder): page views, login analytics, time-on-page, "
        "search logging, and staff dashboards."
    ),
    "SEO_KEYWORDS": (
        "ai user activity monitor,django,user activity,analytics,dashboard,nkscoder,"
        "Nitesh Kumar Singh,open source,page tracking,login analytics"
    ),
    "SEARCH_PLACEHOLDER": "Search users by profile fields…",
    # Optional (regex, label) overrides; default labels come from installed apps/models
    "PATH_LABEL_RULES": [],
    "REPORT_PAGES": [],  # deprecated alias for PATH_LABEL_RULES
    "HOME_SECTION_LABEL": "Home",
    # None = auto-exclude django.contrib.* and this activity app
    "EXCLUDED_APP_LABELS": None,
    "EXCLUDED_CHART_SECTIONS": (),
    "SKIP_PATH_PREFIXES": None,
    "USER_SEARCH_FIELDS": None,
    "USER_SEARCH_FIELD_LIMIT": 12,
    "USER_EXPORT_COLUMNS": None,
    "USER_EXPORT_COLUMN_LIMIT": 10,
    # Template context keys read from request.session (host project optional)
    "SESSION_CONTEXT_KEYS": (),
    "USER_IDENTIFIER_FIELDS": None,
    "USER_LIST_COLUMNS": None,
    "ONLINE_CUTOFF_MINUTES": 10,
    "INACTIVE_DAYS": 30,
}


def get_setting(name):
    key = f"ACTIVITY_{name}"
    if hasattr(settings, key):
        return getattr(settings, key)
    return DEFAULTS[name]
