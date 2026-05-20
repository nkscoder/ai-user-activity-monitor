from typing import Optional

from .models import UserActivityLog
from .utils import (
    build_activity_meta,
    extract_search_params,
    get_client_ip,
    get_request_id,
    parse_device,
)


def log_action(
    *, request, user, action: str,
    object_type: str = "", object_id: str = "",
    status_code: Optional[int] = None,
    meta: Optional[dict] = None,
):
    ua = request.META.get("HTTP_USER_AGENT", "")
    return UserActivityLog.objects.create(
        user=user if user and user.is_authenticated else None,
        event_type=UserActivityLog.EventType.ACTION,
        action=action,
        path=request.path,
        method=request.method,
        status_code=status_code,
        ip_address=get_client_ip(request),
        user_agent=ua,
        device=parse_device(ua),
        session_key=getattr(getattr(request, "session", None), "session_key", "") or "",
        request_id=get_request_id(request),
        referrer=request.META.get("HTTP_REFERER", "")[:500],
        object_type=object_type,
        object_id=str(object_id) if object_id else "",
        meta=meta or {},
    )


def log_search(request, *, user, result_count: Optional[int] = None, extra_meta: Optional[dict] = None):
    """Log a dedicated search action with what the user searched for."""
    search_params = extract_search_params(request)
    if not search_params:
        return None

    meta = build_activity_meta(request, extra_meta)
    if result_count is not None:
        meta["result_count"] = result_count

    return log_action(
        request=request,
        user=user,
        action="search",
        object_type="Search",
        meta=meta,
    )
