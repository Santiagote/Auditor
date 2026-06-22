from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    IsoCharacteristicViewSet, QualityMetricViewSet,
    AuditFindingViewSet, DashboardViewSet,
)

router = DefaultRouter()
router.register(r"characteristics", IsoCharacteristicViewSet, basename="characteristics")
router.register(r"metrics", QualityMetricViewSet, basename="metrics")
router.register(r"findings", AuditFindingViewSet, basename="findings")

urlpatterns = [
    path("dashboard/summary/", DashboardViewSet.as_view({"get": "summary"}), name="dashboard-summary"),
    path("", include(router.urls)),
]
