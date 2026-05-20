from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from .models import UserActivityLog
from .utils import get_client_ip, get_request_id, parse_device

def _base_fields(request):
    ua = request.META.get("HTTP_USER_AGENT", "")
    return dict(
        path=getattr(request, "path", ""),
        method=getattr(request, "method", ""),
        status_code=200,
        ip_address=get_client_ip(request),
        user_agent=ua,
        device=parse_device(ua),
        session_key=getattr(getattr(request, "session", None), "session_key", "") or "",
        request_id=get_request_id(request),
        referrer=request.META.get("HTTP_REFERER", "")[:500],
    )

@receiver(user_logged_in)
def log_login(sender, request, user, **kwargs):
    UserActivityLog.objects.create(
        user=user,
        event_type=UserActivityLog.EventType.ACTION,
        action="login",
        object_type="Auth",
        object_id=str(user.id),
        meta={},
        **_base_fields(request),
    )

@receiver(user_logged_out)
def log_logout(sender, request, user, **kwargs):
    UserActivityLog.objects.create(
        user=user if user and getattr(user, "is_authenticated", False) else None,
        event_type=UserActivityLog.EventType.ACTION,
        action="logout",
        object_type="Auth",
        object_id=str(getattr(user, "id", "")) if user else "",
        meta={},
        **_base_fields(request),
    )

@receiver(user_login_failed)
def log_login_failed(sender, credentials, request, **kwargs):
    # user may be None here (failed)
    UserActivityLog.objects.create(
        user=None,
        event_type=UserActivityLog.EventType.ACTION,
        action="login_failed",
        object_type="Auth",
        object_id="",
        meta={"username": credentials.get("username", "")},
        **_base_fields(request),
    )
