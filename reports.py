from django.contrib.auth import get_user_model
from django.db.models import Count, Max

from .models import UserActivityLog
from .registry import get_user_identifier_field_names


def login_report_qs():
    value_fields = ["user_id"]
    user_model = get_user_model()
    field_names = {f.name for f in user_model._meta.fields}

    for name in get_user_identifier_field_names():
        if name in field_names:
            value_fields.append(f"user__{name}")

    for name in ("first_name", "last_name"):
        if name in field_names and f"user__{name}" not in value_fields:
            value_fields.append(f"user__{name}")

    return (
        UserActivityLog.objects.filter(
            event_type=UserActivityLog.EventType.ACTION,
            action="login",
            user__isnull=False,
        )
        .values(*value_fields)
        .annotate(
            last_login=Max("created_at"),
            total_logins=Count("id"),
        )
        .order_by("-last_login")
    )
