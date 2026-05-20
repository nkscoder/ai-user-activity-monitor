from django.apps import AppConfig

class ActivityConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "activity"
    verbose_name = "AI User Activity Monitor (nkscoder)"

    def ready(self):
        import activity.signals  # noqa
