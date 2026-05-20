from django.utils import timezone

from .models import UserActivityLog
from .services import log_search
from .utils import (
    build_activity_meta,
    get_client_ip,
    get_request_id,
    has_search_request,
    parse_device,
    should_skip_activity_log,
)


class ActivityLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        try:
            path = request.path
            if should_skip_activity_log(path):
                return response

            user = (
                request.user
                if getattr(request, "user", None) and request.user.is_authenticated
                else None
            )
            ua = request.META.get("HTTP_USER_AGENT", "")
            meta = build_activity_meta(request)

            base_fields = dict(
                user=user,
                path=path,
                ip_address=get_client_ip(request),
                user_agent=ua,
                device=parse_device(ua),
                session_key=getattr(getattr(request, "session", None), "session_key", "") or "",
                request_id=get_request_id(request),
                referrer=request.META.get("HTTP_REFERER", "")[:500],
                status_code=getattr(response, "status_code", None),
                meta=meta,
            )

            if request.method == "GET":
                action = "page_view"
                if has_search_request(request):
                    action = "page_view_search"

                UserActivityLog.objects.create(
                    event_type=UserActivityLog.EventType.PAGE_VIEW,
                    action=action,
                    method="GET",
                    started_at=timezone.now(),
                    **base_fields,
                )

                if has_search_request(request) and user:
                    extra = getattr(request, "_activity_search_extra_meta", None)
                    result_count = getattr(request, "_activity_search_result_count", None)
                    log_search(
                        request,
                        user=user,
                        result_count=result_count,
                        extra_meta=extra,
                    )

            elif request.method == "POST" and user:
                action_slug = path.strip("/").replace("/", "_") or "post"
                UserActivityLog.objects.create(
                    event_type=UserActivityLog.EventType.ACTION,
                    action=f"post_{action_slug}"[:120],
                    method="POST",
                    **base_fields,
                )
        except Exception:
            pass

        return response


class RequestIdMiddleware:
    """Sets request._request_id for templates, logging, and page-time JS."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        import uuid

        if not hasattr(request, "_request_id"):
            request._request_id = str(uuid.uuid4())
        return self.get_response(request)
