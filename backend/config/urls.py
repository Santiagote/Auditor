from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.collector.urls")),
    path("api/quality/", include("apps.quality.urls")),
    path("api/reports/", include("apps.reports.urls")),
]
