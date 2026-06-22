from django.db.models import Count
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import AuditEvent
from .serializers import AuditEventSerializer, AuditEventStatsSerializer


class AuditEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditEvent.objects.all()
    serializer_class = AuditEventSerializer
    filterset_fields = ["event_type", "user_email", "user_role", "action", "entity_type"]
    search_fields = ["user_email", "action", "entity_type", "entity_id"]
    ordering_fields = ["timestamp", "collected_at", "event_type"]

    @action(detail=False, methods=["get"])
    def stats(self, request):
        now = timezone.now()
        last_24h = now - timezone.timedelta(hours=24)

        total = AuditEvent.objects.count()
        last_24h_count = AuditEvent.objects.filter(timestamp__gte=last_24h).count()
        by_type = dict(
            AuditEvent.objects.values("event_type")
            .annotate(count=Count("id"))
            .values_list("event_type", "count")
        )
        by_user = dict(
            AuditEvent.objects.values("user_email")
            .annotate(count=Count("id"))
            .order_by("-count")
            .values_list("user_email", "count")[:10]
        )

        serializer = AuditEventStatsSerializer(data={
            "total": total,
            "last_24h": last_24h_count,
            "by_type": by_type,
            "by_user": by_user,
        })
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
