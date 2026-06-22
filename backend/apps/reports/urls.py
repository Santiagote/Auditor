from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditReportViewSet

router = DefaultRouter()
router.register(r"", AuditReportViewSet, basename="reports")

urlpatterns = [
    path("", include(router.urls)),
]
