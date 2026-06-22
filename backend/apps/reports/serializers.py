from rest_framework import serializers
from .models import AuditReport


class AuditReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditReport
        fields = [
            "id", "title", "report_type", "period_start", "period_end",
            "generated_at", "quality_scores", "findings_summary", "pdf_file",
        ]
        read_only_fields = ["id", "generated_at", "pdf_file"]


class GenerateReportSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, default="Informe de Auditoría")
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    report_type = serializers.ChoiceField(
        choices=["AUTOMATIC", "MANUAL"], default="MANUAL"
    )
