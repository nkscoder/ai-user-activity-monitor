from django.conf import settings
from django.db import models


class UserActivityLog(models.Model):
    class EventType(models.TextChoices):
        PAGE_VIEW = "PAGE_VIEW", "Page View"
        ACTION = "ACTION", "Action"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_logs",
    )

    event_type = models.CharField(max_length=20, choices=EventType.choices)
    action = models.CharField(max_length=120, blank=True)
    path = models.CharField(max_length=500)
    method = models.CharField(max_length=10, blank=True)
    status_code = models.PositiveIntegerField(null=True, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    object_type = models.CharField(max_length=80, blank=True)
    object_id = models.CharField(max_length=80, blank=True)
    meta = models.JSONField(default=dict, blank=True)

    # ✅ NEW (advanced)
    session_key = models.CharField(max_length=80, blank=True)
    request_id = models.CharField(max_length=36, blank=True)  # uuid
    referrer = models.CharField(max_length=500, blank=True)

    # parsed fields (auto-fill)
    device = models.CharField(max_length=120, blank=True)   # "Chrome / Windows / Mobile"
    country = models.CharField(max_length=2, blank=True)    # IN
    city = models.CharField(max_length=80, blank=True)      # New Delhi
    location = models.CharField(max_length=120, blank=True) # "New Delhi, IN"
    
    started_at = models.DateTimeField(null=True, blank=True)   # when page opened
    ended_at = models.DateTimeField(null=True, blank=True)     # when leaving page
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)  # time spent

    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["event_type", "created_at"]),
            models.Index(fields=["action", "created_at"]),
            models.Index(fields=["ip_address", "created_at"]),
        ]

    def __str__(self):
        return f"{self.created_at} {self.user_id} {self.event_type} {self.path}"
