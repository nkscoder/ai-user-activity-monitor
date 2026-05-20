from django.core.management.base import BaseCommand
from activity.models import UserActivityLog
from activity.utils import parse_device
import uuid

class Command(BaseCommand):
    help = "Backfill missing activity fields (device/request_id/etc.)"

    def handle(self, *args, **options):
        updated = 0
        qs = UserActivityLog.objects.all().only("id", "user_agent", "device", "request_id")
        for log in qs.iterator():
            changed = False

            if not log.device and log.user_agent:
                log.device = parse_device(log.user_agent)
                changed = True

            if not log.request_id:
                log.request_id = str(uuid.uuid4())
                changed = True

            if changed:
                log.save()
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"Backfilled {updated} rows"))
