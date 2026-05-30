import uuid
import ipaddress
from datetime import datetime

from django.contrib.auth import get_user_model
from django.db.models import CharField, Count, Max, Q, Value
from django.db.models.functions import Coalesce, Concat
from django.utils import timezone

from .conf import get_setting
from .registry import (
    build_user_search_q,
    get_skip_path_prefixes,
    section_name_from_path,
    user_primary_identifier,
)

# Backward-compatible alias
module_name_from_path = section_name_from_path


def get_client_ip(request):
    def _clean_ip(raw: str) -> str:
        if not raw:
            return ""
        value = str(raw).strip().strip('"').strip("'")
        if not value or value.lower() == "unknown":
            return ""

        # X-Forwarded-For may contain multiple values: client, proxy1, proxy2...
        value = value.split(",")[0].strip()

        # Forwarded header can look like: for=1.2.3.4 or for="[2001:db8::1]:443"
        if "for=" in value.lower():
            for_part = value.split("=", 1)[1].strip()
            value = for_part.split(";", 1)[0].strip()

        # Remove brackets around IPv6
        value = value.strip("[]")

        # If host:port for IPv4, remove port
        if value.count(":") == 1 and "." in value:
            value = value.split(":", 1)[0].strip()

        try:
            return str(ipaddress.ip_address(value))
        except ValueError:
            return ""

    candidates = [
        request.META.get("HTTP_CF_CONNECTING_IP"),  # Cloudflare
        request.META.get("HTTP_X_FORWARDED_FOR"),
        request.META.get("HTTP_X_REAL_IP"),
        request.META.get("HTTP_FORWARDED"),
        request.META.get("REMOTE_ADDR"),
    ]
    for candidate in candidates:
        ip = _clean_ip(candidate)
        if ip:
            return ip
    return ""


def get_request_id(request):
    rid = getattr(request, "_request_id", "")
    if rid:
        return rid[:36]

    rid2 = request.META.get("HTTP_X_REQUEST_ID")
    return rid2[:36] if rid2 else ""


def parse_device(user_agent: str) -> str:
    ua = (user_agent or "").lower()

    browser = "Unknown"
    if "edg" in ua:
        browser = "Edge"
    elif "chrome" in ua and "safari" in ua:
        browser = "Chrome"
    elif "firefox" in ua:
        browser = "Firefox"
    elif "safari" in ua and "chrome" not in ua:
        browser = "Safari"

    os_name = "Unknown OS"
    if "windows" in ua:
        os_name = "Windows"
    elif "macintosh" in ua or "mac os" in ua:
        os_name = "macOS"
    elif "android" in ua:
        os_name = "Android"
    elif "iphone" in ua or "ipad" in ua or "ios" in ua:
        os_name = "iOS"
    elif "linux" in ua:
        os_name = "Linux"

    device = "Desktop"
    if "ipad" in ua or "tablet" in ua:
        device = "Tablet"
    elif "mobile" in ua or "android" in ua or "iphone" in ua:
        device = "Mobile"

    return f"{browser} / {os_name} / {device}"


SKIP_LOG_PATHS = (
    "/favicon.ico",
    "/robots.txt",
    "/apple-touch-icon",
)
SKIP_LOG_SUFFIXES = (
    ".ico", ".png", ".jpg", ".jpeg", ".gif", ".css", ".js", ".map",
    ".woff", ".woff2", ".ttf", ".svg",
)


def should_skip_activity_log(path: str) -> bool:
    if not path:
        return True
    if path.startswith(get_skip_path_prefixes()):
        return True
    if path in SKIP_LOG_PATHS or path.startswith(SKIP_LOG_PATHS):
        return True
    if any(path.endswith(suffix) for suffix in SKIP_LOG_SUFFIXES):
        return True
    return False


# Common GET param names used for search across Django apps
SEARCH_PARAM_NAMES = (
    "search",
    "searchvalue",
    "search_by",
    "q",
    "query",
    "keyword",
)


def extract_search_params(request) -> dict:
    """Collect non-empty search-related GET parameters."""
    if request.method != "GET":
        return {}
    found = {}
    for name in SEARCH_PARAM_NAMES:
        raw = request.GET.get(name)
        if raw is None:
            continue
        val = str(raw).strip()
        if val:
            found[name] = val[:500]
    return found


def primary_search_term(search_params: dict) -> str:
    if not search_params:
        return ""
    for key in ("search", "searchvalue", "q", "query", "keyword"):
        if search_params.get(key):
            return search_params[key]
    return next(iter(search_params.values()), "")


def build_activity_meta(request, extra: Optional[dict] = None) -> dict:
    """Build meta JSON for activity logs (query string + structured search)."""
    meta = dict(extra or {})
    qs = request.META.get("QUERY_STRING", "")
    if qs:
        meta["query_string"] = qs[:1000]

    search_params = extract_search_params(request)
    if search_params:
        meta["search_params"] = search_params
        meta["search_term"] = primary_search_term(search_params)
        if request.GET.get("search_by"):
            meta["search_by"] = str(request.GET.get("search_by")).strip()[:120]
    return meta


def has_search_request(request) -> bool:
    return bool(extract_search_params(request))


def user_display_name(user) -> str:
    if not user:
        return "—"
    first = getattr(user, "first_name", "") or ""
    last = getattr(user, "last_name", "") or ""
    name = f"{first} {last}".strip()
    if name:
        return name
    return user_primary_identifier(user)


def get_template_session_context(request) -> dict:
    """Optional keys from request.session for host templates (ACTIVITY_SESSION_CONTEXT_KEYS)."""
    keys = get_setting("SESSION_CONTEXT_KEYS") or ()
    if not keys:
        return {}
    session = getattr(request, "session", None)
    if not session:
        return {}
    return {key: session.get(key) for key in keys}


def get_user_list_queryset(search=""):
    User = get_user_model()
    very_old_date = datetime(1970, 1, 1, tzinfo=timezone.get_current_timezone())

    annotate_kwargs = {}
    field_names = {f.name for f in User._meta.fields}
    if "first_name" in field_names and "last_name" in field_names:
        annotate_kwargs["full_name_text"] = Concat(
            Coalesce("first_name", Value("")),
            Value(" "),
            Coalesce("last_name", Value("")),
            output_field=CharField(),
        )

    qs = User.objects.annotate(
        **annotate_kwargs,
        last_login_at=Max(
            "activity_logs__created_at",
            filter=Q(
                activity_logs__event_type="ACTION",
                activity_logs__action="login",
            ),
        ),
        last_login_sort=Coalesce(
            Max(
                "activity_logs__created_at",
                filter=Q(
                    activity_logs__event_type="ACTION",
                    activity_logs__action="login",
                ),
            ),
            very_old_date,
        ),
        last_activity=Max("activity_logs__created_at"),
        total_logins=Count(
            "activity_logs",
            filter=Q(
                activity_logs__event_type="ACTION",
                activity_logs__action="login",
            ),
        ),
    )

    search_q = build_user_search_q(search)
    if search_q:
        combined = search_q
        if "full_name_text" in annotate_kwargs:
            combined = combined | Q(full_name_text__icontains=search.strip())
        qs = qs.filter(combined)

    return qs.order_by("-last_login_sort", "-last_activity", "-id")

