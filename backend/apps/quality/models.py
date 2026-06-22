from django.db import models


class IsoCharacteristic(models.Model):
    code = models.CharField(max_length=10, unique=True, verbose_name="Código")
    name = models.CharField(max_length=100, verbose_name="Nombre")
    description = models.TextField(verbose_name="Descripción")
    weight = models.FloatField(default=1.0, verbose_name="Peso")

    class Meta:
        verbose_name = "Característica ISO 25010"
        verbose_name_plural = "Características ISO 25010"
        ordering = ["code"]

    def __str__(self):
        return f"[{self.code}] {self.name}"


class IsoSubcharacteristic(models.Model):
    characteristic = models.ForeignKey(
        IsoCharacteristic, on_delete=models.CASCADE,
        related_name="subcharacteristics", verbose_name="Característica"
    )
    name = models.CharField(max_length=100, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")

    class Meta:
        verbose_name = "Subcaracterística ISO 25010"
        verbose_name_plural = "Subcaracterísticas ISO 25010"
        ordering = ["characteristic__code", "name"]

    def __str__(self):
        return f"{self.characteristic.code} - {self.name}"


class QualityMetric(models.Model):
    class Status(models.TextChoices):
        COMPLIANT = "COMPLIANT", "Cumple"
        NON_COMPLIANT = "NON_COMPLIANT", "No cumple"
        WARNING = "WARNING", "En observación"
        NOT_MEASURED = "NOT_MEASURED", "No medido"

    characteristic = models.ForeignKey(
        IsoCharacteristic, on_delete=models.CASCADE,
        related_name="metrics", verbose_name="Característica"
    )
    subcharacteristic = models.ForeignKey(
        IsoSubcharacteristic, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="metrics",
        verbose_name="Subcaracterística"
    )
    metric_name = models.CharField(max_length=100, verbose_name="Nombre de métrica")
    value = models.FloatField(verbose_name="Valor actual")
    target = models.FloatField(verbose_name="Valor objetivo")
    unit = models.CharField(max_length=50, blank=True, verbose_name="Unidad")
    status = models.CharField(
        max_length=20, choices=Status.choices,
        default=Status.NOT_MEASURED, verbose_name="Estado"
    )
    formula = models.TextField(blank=True, verbose_name="Fórmula de cálculo")
    level_descriptions = models.JSONField(
        null=True, blank=True, verbose_name="Descriptores por nivel"
    )
    measured_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de medición")

    class Meta:
        verbose_name = "Métrica de calidad"
        verbose_name_plural = "Métricas de calidad"
        ordering = ["characteristic__code", "metric_name"]

    def __str__(self):
        return f"{self.metric_name}: {self.value}{self.unit} ({self.status})"


class AuditFinding(models.Model):
    class FindingType(models.TextChoices):
        NON_CONFORMITY = "NC", "No Conformidad"
        OBSERVATION = "OBS", "Observación"
        STRENGTH = "STR", "Fortaleza"

    class Severity(models.TextChoices):
        CRITICAL = "CRITICAL", "Crítico"
        MAJOR = "MAJOR", "Mayor"
        MINOR = "MINOR", "Menor"

    class FindingStatus(models.TextChoices):
        OPEN = "OPEN", "Abierto"
        IN_PROGRESS = "IN_PROGRESS", "En progreso"
        CLOSED = "CLOSED", "Cerrado"

    finding_type = models.CharField(
        max_length=10, choices=FindingType.choices,
        verbose_name="Tipo de hallazgo"
    )
    characteristic = models.ForeignKey(
        IsoCharacteristic, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="findings",
        verbose_name="Característica"
    )
    severity = models.CharField(
        max_length=10, choices=Severity.choices,
        verbose_name="Severidad"
    )
    description = models.TextField(verbose_name="Descripción")
    evidence = models.JSONField(null=True, blank=True, verbose_name="Evidencia")
    status = models.CharField(
        max_length=20, choices=FindingStatus.choices,
        default=FindingStatus.OPEN, verbose_name="Estado"
    )
    corrective_action = models.TextField(blank=True, verbose_name="Acción correctiva")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de resolución")

    class Meta:
        verbose_name = "Hallazgo de auditoría"
        verbose_name_plural = "Hallazgos de auditoría"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.finding_type}] {self.description[:60]}"
