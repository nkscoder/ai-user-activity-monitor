from django.contrib import admin

from .models import UserActivityLog
from .registry import get_admin_user_search_fields


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "user",
        "event_type",
        "action",
        "path",
        "method",
        "status_code",
        "ip_address",
    )
    list_filter = ("event_type", "action", "method", "status_code", "created_at")
    search_fields = get_admin_user_search_fields()
    readonly_fields = ("meta",)
    ordering = ("-created_at",)
