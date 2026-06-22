from django.db import models


class AuditEvent(models.Model):
    class EventType(models.TextChoices):
        LOGIN = "LOGIN", "Inicio de sesión"
        LOGIN_FAILED = "LOGIN_FAILED", "Inicio de sesión fallido"
        LOGOUT = "LOGOUT", "Cierre de sesión"
        CAPTURE = "CAPTURE", "Captura de asistencia"
        CAPTURE_FAILED = "CAPTURE_FAILED", "Captura fallida"
        EXCEPTION = "EXCEPTION", "Justificación de inasistencia"
        USER_CREATE = "USER_CREATE", "Creación de usuario"
        USER_UPDATE = "USER_UPDATE", "Actualización de usuario"
        USER_DEACTIVATE = "USER_DEACTIVATE", "Desactivación de usuario"
        USER_REACTIVATE = "USER_REACTIVATE", "Reactivación de usuario"
        PASSWORD_CHANGE = "PASSWORD_CHANGE", "Cambio de contraseña"
        STUDENT_CREATE = "STUDENT_CREATE", "Creación de estudiante"
        STUDENT_UPDATE = "STUDENT_UPDATE", "Actualización de estudiante"
        SCHEDULE_CREATE = "SCHEDULE_CREATE", "Creación de horario"
        SCHEDULE_UPDATE = "SCHEDULE_UPDATE", "Actualización de horario"
        SYSTEM_AVAILABLE = "SYSTEM_AVAILABLE", "Sistema disponible"
        SYSTEM_UNAVAILABLE = "SYSTEM_UNAVAILABLE", "Sistema no disponible"
        API_DOCS_OK = "API_DOCS_OK", "Documentación API disponible"
        API_DOCS_FAIL = "API_DOCS_FAIL", "Documentación API no disponible"

    event_type = models.CharField(max_length=50, choices=EventType.choices, verbose_name="Tipo de evento")
    source = models.CharField(max_length=20, default="SACARF", verbose_name="Fuente")
    user_email = models.EmailField(null=True, blank=True, verbose_name="Correo del usuario")
    user_role = models.CharField(max_length=10, null=True, blank=True, verbose_name="Rol del usuario")
    action = models.CharField(max_length=100, verbose_name="Acción")
    entity_type = models.CharField(max_length=50, blank=True, verbose_name="Tipo de entidad")
    entity_id = models.CharField(max_length=50, blank=True, verbose_name="ID de entidad")
    old_value = models.JSONField(null=True, blank=True, verbose_name="Valor anterior")
    new_value = models.JSONField(null=True, blank=True, verbose_name="Valor nuevo")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="Dirección IP")
    timestamp = models.DateTimeField(verbose_name="Fecha del evento")
    collected_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de recolección")
    raw_response = models.JSONField(null=True, blank=True, verbose_name="Respuesta original")

    class Meta:
        verbose_name = "Evento de auditoría"
        verbose_name_plural = "Eventos de auditoría"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["event_type"]),
            models.Index(fields=["timestamp"]),
            models.Index(fields=["user_email"]),
        ]

    def __str__(self):
        return f"[{self.event_type}] {self.user_email or 'Sistema'} - {self.timestamp}"
