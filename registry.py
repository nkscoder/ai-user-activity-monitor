"""Resolve URL paths to human labels from installed Django apps and models."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Optional

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import models

from .conf import get_setting


def _humanize_slug(slug: str) -> str:
    if not slug:
        return ""
    text = slug.replace("_", " ").replace("-", " ").strip()
    return text.title() if text else ""


@lru_cache(maxsize=1)
def _app_label_map() -> dict[str, str]:
    """URL segment (lowercase) → Django app label."""
    mapping: dict[str, str] = {}
    for app_config in apps.get_app_configs():
        label = app_config.label
        keys = {
            label.lower(),
            label.lower().replace("_", ""),
            app_config.name.split(".")[-1].lower(),
        }
        for key in keys:
            if key:
                mapping.setdefault(key, label)
    return mapping


@lru_cache(maxsize=1)
def _app_display_map() -> dict[str, str]:
    """App label → display name (verbose_name)."""
    result = {}
    for app_config in apps.get_app_configs():
        name = (app_config.verbose_name or app_config.label or "").strip()
        result[app_config.label] = str(name) if name else _humanize_slug(app_config.label)
    return result


@lru_cache(maxsize=1)
def _model_display_index() -> dict[tuple[str, str], str]:
    """(app_label, url_segment) → model verbose name."""
    index: dict[tuple[str, str], str] = {}
    for app_config in apps.get_app_configs():
        for model in app_config.get_models():
            model_name = model._meta.model_name
            label = (
                model._meta.verbose_name_plural
                or model._meta.verbose_name
                or _humanize_slug(model_name)
            )
            keys = {
                model_name.lower(),
                model_name.lower().rstrip("s"),
                model.__name__.lower(),
                model.__name__.lower().rstrip("s"),
            }
            for key in keys:
                if key:
                    index[(app_config.label, key)] = str(label)
    return index


def resolve_app_label(url_segment: str) -> Optional[str]:
    if not url_segment:
        return None
    key = url_segment.lower().replace("-", "_")
    return _app_label_map().get(key) or _app_label_map().get(key.replace("_", ""))


def model_display_for_segment(app_label: str, segment: str) -> Optional[str]:
    if not app_label or not segment:
        return None
    seg = segment.lower().replace("-", "_")
    index = _model_display_index()
    for candidate in (seg, seg.rstrip("s"), seg + "s"):
        hit = index.get((app_label, candidate))
        if hit:
            return hit
    return None


def section_name_from_path(path: str) -> str:
    """
    Label for analytics charts and filters.
    Priority: ACTIVITY_PATH_LABEL_RULES → app verbose_name → model verbose_name → humanized slug.
    """
    custom = page_title_from_path(path)
    if custom:
        return custom

    clean_path = (path or "").split("?", 1)[0].strip("/")
    if not clean_path:
        return get_setting("HOME_SECTION_LABEL")

    segments = [s for s in clean_path.split("/") if s]
    if not segments:
        return get_setting("HOME_SECTION_LABEL")

    first = segments[0]
    app_label = resolve_app_label(first)

    if app_label:
        app_title = _app_display_map().get(app_label) or _humanize_slug(first)
        if len(segments) > 1:
            model_title = model_display_for_segment(app_label, segments[1])
            if model_title:
                return f"{app_title} — {model_title}"
        return app_title

    if len(segments) > 1:
        for app_config in apps.get_app_configs():
            model_title = model_display_for_segment(app_config.label, segments[0])
            if model_title:
                app_title = _app_display_map().get(app_config.label, _humanize_slug(first))
                return f"{app_title} — {model_title}"

    return _humanize_slug(first)


def page_title_from_path(path: str) -> Optional[str]:
    if not path:
        return None
    for pattern, title in get_path_label_rules():
        if re.match(pattern, path):
            return title
    return None


def get_path_label_rules():
    rules = get_setting("PATH_LABEL_RULES")
    if not rules:
        legacy = get_setting("REPORT_PAGES")
        rules = legacy
    return list(rules) if rules else []


@lru_cache(maxsize=1)
def _default_excluded_app_labels() -> frozenset[str]:
    excluded = {
        "admin",
        "auth",
        "contenttypes",
        "sessions",
        "messages",
        "staticfiles",
        "activity",
    }
    for app_config in apps.get_app_configs():
        if app_config.name.startswith("django.contrib."):
            excluded.add(app_config.label)
    return frozenset(excluded)


def get_excluded_chart_sections() -> set[str]:
    """Section titles to hide from visit/time charts (derived from app labels, not static product names)."""
    excluded: set[str] = set()
    extra = get_setting("EXCLUDED_CHART_SECTIONS")
    if extra:
        excluded.update(str(x).strip().lower() for x in extra if str(x).strip())

    labels = get_setting("EXCLUDED_APP_LABELS")
    if labels is None:
        labels = _default_excluded_app_labels()
    else:
        labels = frozenset(labels)

    for app_label in labels:
        try:
            app_config = apps.get_app_config(app_label)
            excluded.add(str(app_config.verbose_name).strip().lower())
        except LookupError:
            pass
        excluded.add(app_label.replace("_", " ").lower())
        excluded.add(_humanize_slug(app_label).lower())

    excluded.add(get_setting("HOME_SECTION_LABEL").strip().lower())
    return excluded


def should_exclude_section(section_title: str) -> bool:
    return section_title.strip().lower() in get_excluded_chart_sections()


def get_skip_path_prefixes() -> tuple[str, ...]:
    prefixes = get_setting("SKIP_PATH_PREFIXES")
    if prefixes:
        return tuple(prefixes)
    base = ("/admin/", "/static/", "/media/")
    try:
        from django.urls import reverse

        activity_prefix = reverse("user_activity_dashboard").rsplit("dashboard", 1)[0]
        if activity_prefix and activity_prefix not in base:
            return base + (activity_prefix,)
    except Exception:
        pass
    return base


def _user_model():
    return get_user_model()


def get_user_identifier_field_names() -> list[str]:
    explicit = get_setting("USER_IDENTIFIER_FIELDS")
    if explicit:
        return list(explicit)

    user_model = _user_model()
    names: list[str] = []
    for name in ("username", "email"):
        if name in [f.name for f in user_model._meta.fields] and name not in names:
            names.append(name)
    for field in user_model._meta.fields:
        if field.name in names or field.name in ("password", "last_login"):
            continue
        if isinstance(field, (models.CharField, models.EmailField)):
            names.append(field.name)
    return names[:3]


def user_primary_identifier(user) -> str:
    if not user:
        return "—"
    for name in get_user_identifier_field_names():
        value = getattr(user, name, None)
        if value not in (None, ""):
            return str(value)
    return f"User #{user.pk}"


def get_user_list_columns() -> list[tuple[str, str]]:
    """(model_field, column_header) for user list table."""
    explicit = get_setting("USER_LIST_COLUMNS")
    if explicit:
        return [(row[0], row[1]) for row in explicit]

    user_model = _user_model()
    columns: list[tuple[str, str]] = []
    id_fields = get_user_identifier_field_names()
    if id_fields:
        field_name = id_fields[0]
        field = user_model._meta.get_field(field_name)
        header = str(field.verbose_name or _humanize_slug(field_name))
        columns.append((field_name, header))

    for field_name in ("email", "username"):
        if field_name in [c[0] for c in columns]:
            continue
        if field_name not in [f.name for f in user_model._meta.fields]:
            continue
        field = user_model._meta.get_field(field_name)
        columns.append((field_name, str(field.verbose_name or _humanize_slug(field_name))))

    return columns[:4]


def get_admin_user_search_fields() -> list[str]:
    fields = ["path", "action", "ip_address"]
    for name in get_user_search_field_names():
        fields.append(f"user__{name}")
    return fields


def get_user_search_field_names() -> list[str]:
    explicit = get_setting("USER_SEARCH_FIELDS")
    if explicit:
        return list(explicit)

    user_model = _user_model()
    names: list[str] = []
    priority = ("email", "first_name", "last_name", "username")
    for name in priority:
        if name in [f.name for f in user_model._meta.fields] and name not in names:
            names.append(name)

    for field in user_model._meta.fields:
        if field.name in names or field.name in ("password", "last_login"):
            continue
        if isinstance(field, (models.CharField, models.EmailField)):
            names.append(field.name)

    return names[: int(get_setting("USER_SEARCH_FIELD_LIMIT"))]


def build_user_search_q(search: str):
    from django.db.models import Q

    search = (search or "").strip()
    if not search:
        return Q()

    q = Q()
    for field_name in get_user_search_field_names():
        q |= Q(**{f"{field_name}__icontains": search})
    return q


def get_user_export_columns() -> list[tuple[str, str]]:
    """
    (model_field_or_callable_key, column_header) for Excel export.
    Keys starting with @ use resolvers on the user instance.
    """
    explicit = get_setting("USER_EXPORT_COLUMNS")
    if explicit:
        return [(row[0], row[1]) for row in explicit]

    user_model = _user_model()
    columns: list[tuple[str, str]] = [("@display", "Display name")]

    for field in user_model._meta.fields:
        if field.name in ("password", "last_login", "is_superuser", "is_staff", "is_active"):
            continue
        if isinstance(field, (models.CharField, models.EmailField)):
            header = str(field.verbose_name or _humanize_slug(field.name))
            columns.append((field.name, header))

    columns.extend([("@last_activity", "Last activity"), ("@total_logins", "Total logins"), ("@last_ip", "Last IP")])
    seen = set()
    unique: list[tuple[str, str]] = []
    for key, header in columns:
        if key in seen:
            continue
        seen.add(key)
        unique.append((key, header))
    return unique[: int(get_setting("USER_EXPORT_COLUMN_LIMIT"))]


def resolve_export_cell(user, field_key: str, *, last_ips: dict, last_activity=None, total_logins=0) -> str:
    from .utils import user_display_name

    if field_key == "@display":
        return user_display_name(user)
    if field_key == "@last_activity":
        return last_activity.strftime("%d-%m-%Y %H:%M:%S") if last_activity else "-"
    if field_key == "@total_logins":
        return total_logins or 0
    if field_key == "@last_ip":
        return last_ips.get(user.id, "-")
    value = getattr(user, field_key, None)
    if value is None or value == "":
        return "-"
    return value
