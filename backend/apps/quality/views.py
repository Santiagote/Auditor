from django.utils import timezone
from django.db.models import Count, Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.collector.models import AuditEvent
from apps.collector.serializers import AuditEventSerializer
from .models import IsoCharacteristic, QualityMetric, AuditFinding
from .serializers import (
    IsoCharacteristicSerializer, QualityMetricSerializer,
    AuditFindingSerializer,
)
from .metrics_engine import get_radar_data


class IsoCharacteristicViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = IsoCharacteristic.objects.prefetch_related("subcharacteristics").all()
    serializer_class = IsoCharacteristicSerializer


class QualityMetricViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = QualityMetric.objects.select_related(
        "characteristic", "subcharacteristic"
    ).all()
    serializer_class = QualityMetricSerializer
    filterset_fields = ["characteristic", "status", "characteristic__code"]
    ordering_fields = ["-measured_at"]

    @action(detail=False, methods=["get"])
    def latest(self, request):
        metrics = []
        for char in IsoCharacteristic.objects.all():
            latest = QualityMetric.objects.filter(characteristic=char).order_by("-measured_at").first()
            if latest:
                metrics.append(latest)
        serializer = self.get_serializer(metrics, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def levels(self, request):
        codes = request.query_params.getlist("code")
        qs = QualityMetric.objects.select_related("characteristic").filter(
            metric_name__in=[
                "Protección contra ataques de fuerza bruta",
                "Precisión del backend para rechazar registros inválidos",
                "Resiliencia ante interrupciones en servicios AWS",
                "Aislamiento e impacto operativo al realizar cambios",
            ]
        ).order_by("-measured_at")
        if codes:
            qs = qs.filter(characteristic__code__in=codes)
        seen = {}
        for m in qs:
            if m.characteristic.code not in seen:
                seen[m.characteristic.code] = m
        serializer = self.get_serializer(list(seen.values()), many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def history(self, request):
        char_code = request.query_params.get("characteristic")
        days = int(request.query_params.get("days", 7))
        since = timezone.now() - timezone.timedelta(days=days)

        qs = QualityMetric.objects.filter(measured_at__gte=since)
        if char_code:
            qs = qs.filter(characteristic__code=char_code)
        qs = qs.order_by("-measured_at")

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class AuditFindingViewSet(viewsets.ModelViewSet):
    queryset = AuditFinding.objects.select_related("characteristic").all()
    serializer_class = AuditFindingSerializer
    filterset_fields = ["finding_type", "severity", "status", "characteristic"]
    search_fields = ["description", "corrective_action"]
    ordering_fields = ["-created_at"]

    def perform_update(self, serializer):
        if serializer.validated_data.get("status") == "CLOSED":
            serializer.save(resolved_at=timezone.now())
        else:
            serializer.save()

    @action(detail=False, methods=["get"])
    def stats(self, request):
        by_type = dict(
            AuditFinding.objects.values("finding_type")
            .annotate(count=Count("id"))
            .values_list("finding_type", "count")
        )
        by_severity = dict(
            AuditFinding.objects.values("severity")
            .annotate(count=Count("id"))
            .values_list("severity", "count")
        )
        by_status = dict(
            AuditFinding.objects.values("status")
            .annotate(count=Count("id"))
            .values_list("status", "count")
        )
        return Response({
            "by_type": by_type,
            "by_severity": by_severity,
            "by_status": by_status,
        })


class DashboardViewSet(viewsets.ViewSet):

    @action(detail=False, methods=["get"])
    def summary(self, request):
        radar_data = get_radar_data()
        scores = list(radar_data.values())
        global_score = round(sum(scores) / len(scores), 1) if scores else 0.0

        total_events = AuditEvent.objects.count()
        open_findings = AuditFinding.objects.filter(status="OPEN").count()
        compliant = QualityMetric.objects.filter(status="COMPLIANT").count()
        non_compliant = QualityMetric.objects.exclude(status="COMPLIANT").count()

        last_events = AuditEvent.objects.order_by("-timestamp")[:10]
        events_serializer = AuditEventSerializer(last_events, many=True)

        metrics = QualityMetric.objects.select_related("characteristic").filter(
            metric_name__in=[
                "Protección contra ataques de fuerza bruta",
                "Precisión del backend para rechazar registros inválidos",
                "Resiliencia ante interrupciones en servicios AWS",
                "Aislamiento e impacto operativo al realizar cambios",
            ]
        ).order_by("-measured_at")
        latest_metrics = {}
        for m in metrics:
            if m.characteristic.code not in latest_metrics:
                latest_metrics[m.characteristic.code] = {
                    "code": m.characteristic.code,
                    "name": m.characteristic.name,
                    "aspect": m.metric_name,
                    "level": int(m.value),
                    "max_level": int(m.target),
                    "label": f"Nivel {int(m.value)}/5",
                    "description": m.formula,
                    "levels": m.level_descriptions,
                    "status": m.status,
                }

        return Response({
            "radar_data": radar_data,
            "global_score": global_score,
            "total_events": total_events,
            "open_findings": open_findings,
            "compliant_metrics": compliant,
            "non_compliant_metrics": non_compliant,
            "last_events": events_serializer.data,
            "maturity_levels": list(latest_metrics.values()),
        })
