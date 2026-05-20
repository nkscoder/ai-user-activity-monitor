from django.urls import path
from .views import *

urlpatterns = [
    path("license/", license_page, name="activity_license"),
    path("page-time/", page_time, name="page_time"),
    path("dashboard/users/", user_list, name="activity_user_list"),
    path("dashboard/users/<int:user_id>/", user_detail, name="activity_user_detail"),
    path("dashboard/user-activity/", user_activity_dashboard, name="user_activity_dashboard"),
    path("dashboard/users/export-excel/", export_user_list_excel, name="export_user_list_excel"),
]
