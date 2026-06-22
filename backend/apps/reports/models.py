from django.db import models


class AuditReport(models.Model):
    class ReportType(models.TextChoices):
        AUTOMATIC = "AUTOMATIC", "Automático"
        MANUAL = "MANUAL", "Manual"

    title = models.CharField(max_length=200, verbose_name="Título")
    report_type = models.CharField(
        max_length=20, choices=ReportType.choices,
        verbose_name="Tipo de informe"
    )
    period_start = models.DateField(verbose_name="Inicio del período")
    period_end = models.DateField(verbose_name="Fin del período")
    generated_at = models.DateTimeField(auto_now_add=True, verbose_name="Generado el")
    quality_scores = models.JSONField(default=dict, verbose_name="Puntajes de calidad")
    findings_summary = models.JSONField(default=dict, verbose_name="Resumen de hallazgos")
    pdf_file = models.FileField(
        upload_to="reports/", null=True, blank=True,
        verbose_name="Archivo PDF"
    )

    class Meta:
        verbose_name = "Informe de auditoría"
        verbose_name_plural = "Informes de auditoría"
        ordering = ["-generated_at"]

    def __str__(self):
        return f"{self.title} ({self.period_start} - {self.period_end})"
