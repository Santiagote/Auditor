import logging
from datetime import date, timedelta
from celery import shared_task
from django.utils import timezone
from .models import AuditReport
from .views import AuditReportViewSet
from apps.quality.metrics_engine import calculate_all

logger = logging.getLogger(__name__)


@shared_task
def generate_auto_report():
    logger.info("Generando informe automático diario")
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)

    calculate_all()

    from apps.quality.models import AuditFinding, IsoCharacteristic
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
        title=f"Informe Automático Semanal {week_ago} al {today}",
        report_type="AUTOMATIC",
        period_start=week_ago,
        period_end=today,
        quality_scores=scores,
        findings_summary=findings_summary,
    )

    from .pdf_generator import AuditReportPDF
    import os
    from django.conf import settings

    pdf_buffer = AuditReportPDF(report).build()

    reports_dir = os.path.join(settings.MEDIA_ROOT, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    filename = f"auto_report_{report.id}_{today.isoformat()}.pdf"
    filepath = os.path.join(reports_dir, filename)

    with open(filepath, "wb") as f:
        f.write(pdf_buffer.getvalue())

    report.pdf_file.name = f"reports/{filename}"
    report.save(update_fields=["pdf_file"])

    logger.info(f"Informe automático generado: {filename}")
    return report.id
