from django import template

from activity.utils import user_display_name

register = template.Library()


@register.filter
def user_display(user):
    return user_display_name(user)


@register.filter
def user_field(user, field_name):
    """Read a field from AUTH_USER_MODEL for list tables."""
    if not user or not field_name:
        return "—"
    value = getattr(user, field_name, None)
    if value in (None, ""):
        return "—"
    return value


@register.filter
def get_item(d, key):
    if not d:
        return None
    return d.get(key)

@register.filter
def meta_search_term(log):
    """Display primary search text from log.meta."""
    meta = getattr(log, "meta", None) or {}
    if not isinstance(meta, dict):
        return ""
    if meta.get("search_term"):
        return meta["search_term"]
    params = meta.get("search_params")
    if isinstance(params, dict) and params:
        from activity.utils import primary_search_term
        return primary_search_term(params)
    if isinstance(meta.get("search"), str):
        return meta["search"]
    return ""


@register.filter
def duration_hms(seconds):
    """
    Convert seconds -> HH:MM:SS (or MM:SS if < 1 hour)
    """
    if seconds is None:
        return "-"
    try:
        seconds = int(seconds)
    except (TypeError, ValueError):
        return "-"

    if seconds < 0:
        seconds = 0

    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60

    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

# @register.filter
# def duration_hms(seconds):
#     if seconds is None:
#         return "-"
#     seconds = int(seconds)
#     h = seconds // 3600
#     m = (seconds % 3600) // 60
#     s = seconds % 60
#     if h > 0:
#         return f"{h:02d}:{m:02d}:{s:02d}"
#     return f"{m:02d}:{s:02d}"
