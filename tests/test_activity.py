import pytest
from django.contrib.auth.models import User

from activity.conf import get_setting
from activity.models import UserActivityLog
from activity.registry import section_name_from_path, should_exclude_section
from activity.utils import should_skip_activity_log, user_display_name


@pytest.mark.django_db
def test_create_activity_log():
    user = User.objects.create_user(username="ci_user", email="ci@example.com")
    log = UserActivityLog.objects.create(
        user=user,
        event_type=UserActivityLog.EventType.PAGE_VIEW,
        action="page_view",
        path="/dashboard/",
        method="GET",
    )
    assert log.pk
    assert log.user_id == user.pk


def test_conf_defaults():
    assert get_setting("PACKAGE_NAME") == "ai-user-activity-monitor"
    assert "nkscoder" in get_setting("GITHUB_URL")


def test_section_name_from_path():
    assert section_name_from_path("/") == get_setting("HOME_SECTION_LABEL")
    title = section_name_from_path("/unknown-module/page/")
    assert title


def test_should_skip_static_paths():
    assert should_skip_activity_log("/static/app.js") is True
    assert should_skip_activity_log("/dashboard/") is False


def test_should_exclude_home_section():
    assert should_exclude_section(get_setting("HOME_SECTION_LABEL")) is True


def test_user_display_name():
    user = User(username="alice", first_name="Alice", last_name="Smith", email="a@ex.com")
    assert user_display_name(user) == "Alice Smith"
