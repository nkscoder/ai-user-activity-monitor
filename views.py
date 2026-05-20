import json
from datetime import timedelta

import openpyxl
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Count, Max, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from django.contrib.auth import get_user_model

from .conf import get_setting
from .models import UserActivityLog
from .registry import (
    get_user_export_columns,
    resolve_export_cell,
    section_name_from_path,
    should_exclude_section,
)
from .registry import get_user_list_columns
from .utils import get_template_session_context, get_user_list_queryset, user_display_name


def _section_filter_from_request(request):
    return (request.GET.get("section") or request.GET.get("module") or "").strip()

staff_required = user_passes_test(lambda u: u.is_active and (u.is_staff or u.is_superuser))


def license_page(request):
    """Public MIT license page (SEO-friendly, open source by nkscoder)."""
    return render(request, "activity/license.html", {})


@csrf_exempt
@require_POST
def page_time(request):
    try:
        raw = request.body.decode("utf-8").strip()
        if not raw:
            return JsonResponse({"ok": False, "msg": "empty body"}, status=400)

        data = json.loads(raw)
        request_id = data.get("request_id")
        duration = int(data.get("duration_seconds", 0))

        if not request_id:
            return JsonResponse({"ok": False, "msg": "missing request_id"}, status=400)

        log = (
            UserActivityLog.objects.filter(
                request_id=request_id,
                event_type=UserActivityLog.EventType.PAGE_VIEW,
            )
            .order_by("-created_at")
            .first()
        )

        if not log:
            return JsonResponse({"ok": False, "msg": "not found"}, status=404)

        log.duration_seconds = duration
        log.ended_at = timezone.now()
        log.save(update_fields=["duration_seconds", "ended_at"])

        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"ok": False, "msg": str(e)}, status=500)


@login_required(login_url="login")
@staff_required
def user_list(request):
    search = (request.GET.get("search") or "").strip()
    section_filter = _section_filter_from_request(request)

    try:
        per_page = int(request.GET.get("per_page") or 12)
    except ValueError:
        per_page = 12

    per_page = per_page if per_page in (10, 12, 20, 50, 100, 200) else 12

    qs = get_user_list_queryset(search=search)

    if section_filter:
        section_user_ids = set()
        section_logs = (
            UserActivityLog.objects.filter(event_type="PAGE_VIEW")
            .exclude(path__icontains="favicon")
            .exclude(user_id__isnull=True)
            .values("user_id", "path")
            .iterator()
        )
        for row in section_logs:
            if section_name_from_path(row["path"]) == section_filter:
                section_user_ids.add(row["user_id"])
        qs = qs.filter(id__in=section_user_ids)

    paginator = Paginator(qs, per_page)
    page_number = request.GET.get("page") or 1
    page_obj = paginator.get_page(page_number)

    if search:
        request._activity_search_result_count = paginator.count
        request._activity_search_extra_meta = {"section": "activity_user_list"}

    user_ids = [u.id for u in page_obj.object_list]
    last_ips = {}

    login_logs = (
        UserActivityLog.objects.filter(
            event_type="ACTION", action="login", user_id__in=user_ids
        )
        .order_by("user_id", "-created_at")
        .values("user_id", "ip_address")
    )

    for row in login_logs:
        if row["user_id"] not in last_ips:
            last_ips[row["user_id"]] = row["ip_address"] or "-"

    return render(
        request,
        "activity/dashboard_user_list.html",
        {
            "users": page_obj.object_list,
            "page_obj": page_obj,
            "paginator": paginator,
            "search": search,
            "per_page": per_page,
            "total_users": paginator.count,
            "last_ips": last_ips,
            "section_filter": section_filter,
            "search_placeholder": get_setting("SEARCH_PLACEHOLDER"),
            "user_list_columns": get_user_list_columns(),
            **get_template_session_context(request),
        },
    )


@login_required(login_url="login")
@staff_required
def user_detail(request, user_id):
    user = get_object_or_404(get_user_model(), pk=user_id)

    try:
        per_page = int(request.GET.get("per_page") or 10)
    except ValueError:
        per_page = 10
    per_page = per_page if per_page in (10, 25, 50, 100) else 10

    page_number = request.GET.get("page") or 1

    logs_qs = UserActivityLog.objects.filter(user=user).order_by("-created_at")

    paginator = Paginator(logs_qs, per_page)
    page_obj = paginator.get_page(page_number)

    total_time = (
        UserActivityLog.objects.filter(user=user, duration_seconds__isnull=False).aggregate(
            t=Sum("duration_seconds")
        )["t"]
        or 0
    )

    page_time_rows = (
        UserActivityLog.objects.filter(
            user=user, event_type="PAGE_VIEW", duration_seconds__isnull=False
        )
        .values("path")
        .annotate(total=Sum("duration_seconds"))
        .order_by("-total")[:200]
    )

    total_logs = logs_qs.count()
    last_seen = logs_qs.aggregate(m=Max("created_at"))["m"]

    return render(
        request,
        "activity/dashboard_user_detail.html",
        {
            "user_obj": user,
            "total_time": total_time,
            "total_logs": total_logs,
            "last_seen": last_seen,
            "page_time": page_time_rows,
            "logs": page_obj.object_list,
            "page_obj": page_obj,
            "per_page": per_page,
            "total_logs_count": paginator.count,
            **get_template_session_context(request),
        },
    )


def _user_type_label(u) -> str:
    if getattr(u, "is_superuser", False):
        return "Administrator"
    if getattr(u, "is_staff", False):
        return "Staff"
    return "User"


@login_required(login_url="login")
@staff_required
def user_activity_dashboard(request):
    now = timezone.now()
    online_cutoff = now - timedelta(minutes=10)
    inactive_cutoff = now - timedelta(days=30)

    users = get_user_model().objects.annotate(
        last_login_at=Max(
            "activity_logs__created_at",
            filter=Q(activity_logs__event_type="ACTION", activity_logs__action="login"),
        ),
        last_access_at=Max(
            "activity_logs__created_at",
            filter=Q(activity_logs__event_type="PAGE_VIEW"),
        ),
    )

    online_users_qs = users.filter(last_access_at__gte=online_cutoff).order_by("-last_access_at")
    online_count = online_users_qs.count()
    active_users = online_users_qs[:200]

    inactive_users = users.filter(
        Q(last_access_at__lt=inactive_cutoff) | Q(last_access_at__isnull=True)
    ).order_by("last_access_at")[:500]

    type_counts = {"Administrator": 0, "Staff": 0, "User": 0}
    for u in users.only("id", "is_superuser", "is_staff"):
        type_counts[_user_type_label(u)] += 1

    day_cutoff = now - timedelta(days=1)
    week_cutoff = now - timedelta(days=7)
    month_cutoff = now - timedelta(days=30)
    year_cutoff = now - timedelta(days=365)

    last_login_counts = {
        "Last day": users.filter(last_login_at__gte=day_cutoff).count(),
        "Last week": users.filter(
            last_login_at__lt=day_cutoff, last_login_at__gte=week_cutoff
        ).count(),
        "Last month": users.filter(
            last_login_at__lt=week_cutoff, last_login_at__gte=month_cutoff
        ).count(),
        "Last year": users.filter(
            last_login_at__lt=month_cutoff, last_login_at__gte=year_cutoff
        ).count(),
        "More than a year": users.filter(last_login_at__lt=year_cutoff).count(),
        "Never logged in": users.filter(last_login_at__isnull=True).count(),
    }

    # Time spent (needs duration_seconds from page-time tracker)
    duration_rows = (
        UserActivityLog.objects.filter(
            event_type="PAGE_VIEW", duration_seconds__isnull=False
        )
        .values("path")
        .annotate(total=Sum("duration_seconds"))
        .order_by("-total")[:200]
    )
    time_bucket = {}
    for row in duration_rows:
        title = section_name_from_path(row["path"])
        time_bucket[title] = time_bucket.get(title, 0) + int(row["total"] or 0)
    time_items = sorted(time_bucket.items(), key=lambda x: x[1], reverse=True)
    top_time_labels = [k for k, _ in time_items][:10]
    top_time_values = [v for _, v in time_items][:10]

    # Visits by app section (unique users per section; labels from installed apps/models).
    visit_user_sets = {}
    visit_rows = (
        UserActivityLog.objects.filter(event_type="PAGE_VIEW")
        .exclude(path__icontains="favicon")
        .exclude(user_id__isnull=True)
        .values("user_id", "path")
        .iterator()
    )
    for row in visit_rows:
        title = section_name_from_path(row["path"])
        if should_exclude_section(title):
            continue
        visit_user_sets.setdefault(title, set()).add(row["user_id"])

    visit_items = sorted(
        [(module, len(user_ids)) for module, user_ids in visit_user_sets.items()],
        key=lambda x: x[1],
        reverse=True,
    )
    top_visit_labels = [k for k, _ in visit_items][:10]
    top_visit_values = [v for _, v in visit_items][:10]

    recent_logs = (
        UserActivityLog.objects.select_related("user")
        .exclude(path__icontains="favicon")
        .order_by("-created_at")[:25]
    )
    total_activity_logs = UserActivityLog.objects.count()
    login_labels = list(last_login_counts.keys())
    login_values = list(last_login_counts.values())
    type_labels = list(type_counts.keys())
    type_values = list(type_counts.values())

    context = {
        "online_count": online_count,
        "active_users": active_users,
        "inactive_users": inactive_users,
        "top_time_labels": top_time_labels,
        "top_time_values": top_time_values,
        "login_labels": login_labels,
        "login_values": login_values,
        "type_labels": type_labels,
        "type_values": type_values,
        "top_visit_labels": top_visit_labels,
        "top_visit_values": top_visit_values,
        "top_visit_labels_json": json.dumps(top_visit_labels),
        "top_visit_filters_json": json.dumps(top_visit_labels),
        "top_visit_values_json": json.dumps(top_visit_values),
        "top_time_labels_json": json.dumps(top_time_labels),
        "top_time_values_json": json.dumps(top_time_values),
        "login_labels_json": json.dumps(login_labels),
        "recent_logs": recent_logs,
        "total_activity_logs": total_activity_logs,
        "login_values_json": json.dumps(login_values),
        "type_labels_json": json.dumps(type_labels),
        "type_values_json": json.dumps(type_values),
        "online_cutoff_minutes": get_setting("ONLINE_CUTOFF_MINUTES"),
        "inactive_days": get_setting("INACTIVE_DAYS"),
        "active_tab": "user_activity_dashboard",
        "user_list_columns": get_user_list_columns(),
        **get_template_session_context(request),
    }

    return render(request, "activity/user_activity_dashboard.html", context)


@login_required(login_url="login")
@staff_required
def export_user_list_excel(request):
    search = (request.GET.get("search") or "").strip()
    section_filter = _section_filter_from_request(request)
    qs = get_user_list_queryset(search=search)

    if section_filter:
        section_user_ids = set()
        section_logs = (
            UserActivityLog.objects.filter(event_type="PAGE_VIEW")
            .exclude(path__icontains="favicon")
            .exclude(user_id__isnull=True)
            .values("user_id", "path")
            .iterator()
        )
        for row in section_logs:
            if section_name_from_path(row["path"]) == section_filter:
                section_user_ids.add(row["user_id"])
        qs = qs.filter(id__in=section_user_ids)

    user_ids = list(qs.values_list("id", flat=True))
    last_ips = {}

    login_logs = (
        UserActivityLog.objects.filter(
            event_type="ACTION", action="login", user_id__in=user_ids
        )
        .order_by("user_id", "-created_at")
        .values("user_id", "ip_address")
    )

    for row in login_logs:
        if row["user_id"] not in last_ips:
            last_ips[row["user_id"]] = row["ip_address"] or "-"

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Users"

    export_columns = get_user_export_columns()
    ws.append(["S.No."] + [header for _, header in export_columns])

    for index, u in enumerate(qs, start=1):
        row = [index]
        for field_key, _header in export_columns:
            row.append(
                resolve_export_cell(
                    u,
                    field_key,
                    last_ips=last_ips,
                    last_activity=u.last_activity,
                    total_logins=u.total_logins,
                )
            )
        ws.append(row)

    for column_cells in ws.columns:
        max_length = 0
        column_letter = column_cells[0].column_letter
        for cell in column_cells:
            cell_value = str(cell.value) if cell.value is not None else ""
            if len(cell_value) > max_length:
                max_length = len(cell_value)
        ws.column_dimensions[column_letter].width = min(max_length + 2, 35)

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="user_activity_list.xlsx"'
    wb.save(response)
    return response
