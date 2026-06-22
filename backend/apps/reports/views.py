import os
from django.conf import settings
from django.http import FileResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import AuditReport
from .serializers import AuditReportSerializer, GenerateReportSerializer
from .pdf_generator import AuditReportPDF
from apps.quality.models import AuditFinding, IsoCharacteristic
from apps.collector.models import AuditEvent
from django.utils import timezone


class AuditReportViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditReport.objects.all()
    serializer_class = AuditReportSerializer
    ordering_fields = ["-generated_at"]

    @action(detail=False, methods=["post"])
    def generate(self, request):
        serializer = GenerateReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        title = serializer.validated_data.get(
            "title",
            f"Informe de Auditoría {serializer.validated_data['period_start']} "
            f"al {serializer.validated_data['period_end']}"
        )

        scores = {}
        for char in IsoCharacteristic.objects.all():
            metrics = char.metrics.all()
            if metrics.exists():
                latest = metrics.order_by("-measured_at").first()
                from apps.quality.metrics_engine import get_radar_data
                scores = get_radar_data()

        findings = AuditFinding.objects.all()
        findings_summary = {
            "NC": findings.filter(finding_type="NC").count(),
            "OBS": findings.filter(finding_type="OBS").count(),
            "STR": findings.filter(finding_type="STR").count(),
            "total": findings.count(),
            "open": findings.filter(status="OPEN").count(),
            "closed": findings.filter(status="CLOSED").count(),
        }

        report = AuditReport.objects.create(
            title=title,
            report_type=serializer.validated_data["report_type"],
            period_start=serializer.validated_data["period_start"],
            period_end=serializer.validated_data["period_end"],
            quality_scores=scores,
            findings_summary=findings_summary,
        )

        pdf_buffer = AuditReportPDF(report).build()

        reports_dir = os.path.join(settings.MEDIA_ROOT, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        filename = f"audit_report_{report.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(reports_dir, filename)

        with open(filepath, "wb") as f:
            f.write(pdf_buffer.getvalue())

        report.pdf_file.name = f"reports/{filename}"
        report.save(update_fields=["pdf_file"])

        return Response(
            AuditReportSerializer(report).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        report = self.get_object()
        if not report.pdf_file:
            return Response(
                {"detail": "El archivo PDF no está disponible"},
                status=status.HTTP_404_NOT_FOUND,
            )
        filepath = report.pdf_file.path
        if not os.path.exists(filepath):
            return Response(
                {"detail": "El archivo no existe en el servidor"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return FileResponse(
            open(filepath, "rb"),
            as_attachment=True,
            filename=f"informe_auditoria_{report.id}.pdf",
        )

    @action(detail=False, methods=["get"])
    def scheduled(self, request):
        return Response({
            "scheduled": True,
            "interval": "daily",
            "time": "00:00",
            "task": "apps.reports.tasks.generate_auto_report",
        })
