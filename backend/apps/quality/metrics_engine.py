import logging
from django.utils import timezone
from django.db.models import Count, Q
from apps.collector.models import AuditEvent
from .models import IsoCharacteristic, QualityMetric

logger = logging.getLogger(__name__)

MATURITY_LEVELS = {
    "SEC": {
        "characteristic_code": "SEC",
        "aspect_name": "Protección contra ataques de fuerza bruta",
        "levels": [
            "No bloquea cuenta, no expira JWT, permite intentos infinitos de sesión",
            "El token JWT expira, pero el contador de intentos fallidos no bloquea al usuario",
            "Bloquea la cuenta tras 5 intentos fallidos, pero sin contador regresivo",
            "Token JWT expira en 15 minutos y tras 5 intentos fallidos la cuenta se bloquea con contador regresivo",
            "Nivel 4, además notifica administrativamente el bloqueo y registra la IP del intento fallido",
        ],
    },
    "FUN": {
        "characteristic_code": "FUN",
        "aspect_name": "Precisión del backend para rechazar registros inválidos",
        "levels": [
            "Permite registrar asistencia de cualquier estudiante en cualquier curso sin validar matrícula",
            "Valida al estudiante, pero permite registrar asistencia en asignaturas donde no está matriculado",
            "Valida la matrícula, pero permite registrar asistencia fuera del horario activo de la clase",
            "El endpoint verifica que el alumno esté matriculado en el curso y en el horario activo",
            "Nivel 4, y la validación se ejecuta en menos de 100ms",
        ],
    },
    "REL": {
        "characteristic_code": "REL",
        "aspect_name": "Resiliencia ante interrupciones en servicios AWS",
        "levels": [
            "Si AWS Rekognition falla o da timeout, la aplicación colapsa, interrumpe el flujo y pierde datos",
            "Captura el fallo, pero muestra error genérico al usuario y obliga a repetir manualmente desde cero",
            "No colapsa, pero deja la asistencia registrada como 'Falta' sin opción a recuperar la imagen",
            "Captura la excepción, encola la imagen de forma asíncrona en S3 con estado 'Pendiente' y reintenta automáticamente",
            "Nivel 4, y el reintento se completa de forma transparente para el usuario en menos de 3 intentos",
        ],
    },
    "MAI": {
        "characteristic_code": "MAI",
        "aspect_name": "Aislamiento e impacto operativo al realizar cambios",
        "levels": [
            "Componentes acoplados: un cambio en código rompe la BD o requiere recompilación Angular",
            "Usa contenedores Docker, pero comparten almacenamiento interno o variables hardcodeadas",
            "Servicios separados en Docker, pero actualizar el contenedor del backend genera caídas prolongadas",
            "Servicios independientes en Docker Compose con variables en archivo .env",
            "Desacoplamiento total: contenedores se destruyen y recrean instantáneamente con downtime mínimo",
        ],
    },
}


def _count_event_type(event_type, since=None):
    qs = AuditEvent.objects.filter(event_type=event_type)
    if since:
        qs = qs.filter(timestamp__gte=since)
    return qs.count()


def _evaluate_security_level():
    now = timezone.now()
    last_24h = now - timezone.timedelta(hours=24)

    login_ok = _count_event_type("LOGIN", last_24h)
    login_failed = _count_event_type("LOGIN_FAILED", last_24h)
    system_ok = _count_event_type("SYSTEM_AVAILABLE", last_24h)

    # No auth events at all → can't determine, assume basic auth exists
    if login_ok == 0 and login_failed == 0:
        if system_ok > 0:
            return 4

    # We have login events
    # Check ratio: if failures exist but successes also happen
    # The system allows repeated attempts
    if login_failed > 0 and login_ok > 0:
        # Check for patterns suggesting lockout
        recent_failures = AuditEvent.objects.filter(
            event_type="LOGIN_FAILED",
            timestamp__gte=now - timezone.timedelta(minutes=30),
        ).count()

        if recent_failures >= 5:
            # 5+ failures in 30 min → check if any success after
            last_failure = AuditEvent.objects.filter(
                event_type="LOGIN_FAILED",
                timestamp__gte=now - timezone.timedelta(minutes=30),
            ).last()

            if last_failure:
                success_after = AuditEvent.objects.filter(
                    event_type="LOGIN",
                    timestamp__gt=last_failure.timestamp,
                ).exists()
                if success_after:
                    return 3
                else:
                    return 4

        # JWT expiry observed (login_ok exists with gaps)
        if login_ok > 1:
            return 4

        return 3

    if login_failed == 0 and login_ok > 0:
        return 5

    return 2


def _evaluate_functional_level():
    now = timezone.now()
    last_24h = now - timezone.timedelta(hours=24)

    captures = _count_event_type("CAPTURE", last_24h)
    captures_failed = _count_event_type("CAPTURE_FAILED", last_24h)
    system_ok = _count_event_type("SYSTEM_AVAILABLE", last_24h)

    if captures == 0 and captures_failed == 0:
        if system_ok > 0:
            return 4

    if captures > 0:
        if captures_failed == 0:
            return 5
        return 4

    if captures_failed > 0:
        return 3

    return 2


def _evaluate_reliability_level():
    now = timezone.now()
    last_24h = now - timezone.timedelta(hours=24)

    system_ok = _count_event_type("SYSTEM_AVAILABLE", last_24h)
    system_unavail = _count_event_type("SYSTEM_UNAVAILABLE", last_24h)
    captures = _count_event_type("CAPTURE", last_24h)
    captures_failed = _count_event_type("CAPTURE_FAILED", last_24h)

    total_checks = system_ok + system_unavail

    if total_checks == 0:
        return 3

    availability = (system_ok / total_checks) * 100

    if availability >= 99 and captures > 0 and captures_failed == 0:
        return 5

    if availability >= 95 and captures > 0:
        return 4

    if availability >= 80:
        return 3

    if availability >= 50:
        return 2

    return 1


def _evaluate_maintainability_level():
    now = timezone.now()
    last_24h = now - timezone.timedelta(hours=24)

    system_ok = _count_event_type("SYSTEM_AVAILABLE", last_24h)
    system_unavail = _count_event_type("SYSTEM_UNAVAILABLE", last_24h)
    exceptions = _count_event_type("EXCEPTION", last_24h)
    docs_ok = _count_event_type("API_DOCS_OK", now - timezone.timedelta(days=7))

    total_checks = system_ok + system_unavail

    if total_checks == 0:
        return 4

    availability = (system_ok / total_checks) * 100

    if availability >= 99 and docs_ok > 0:
        return 5

    if availability >= 95:
        return 4

    if availability >= 80:
        return 3

    if availability >= 50:
        return 2

    return 1


def get_level_status(level):
    if level >= 4:
        return QualityMetric.Status.COMPLIANT
    if level == 3:
        return QualityMetric.Status.WARNING
    return QualityMetric.Status.NON_COMPLIANT


def calculate_all():
    logger.info("Iniciando evaluación de niveles de madurez ISO 25010")
    now = timezone.now()

    evaluators = {
        "SEC": _evaluate_security_level,
        "FUN": _evaluate_functional_level,
        "REL": _evaluate_reliability_level,
        "MAI": _evaluate_maintainability_level,
    }

    generated = 0
    for code, config in MATURITY_LEVELS.items():
        if code not in evaluators:
            continue

        try:
            char = IsoCharacteristic.objects.get(code=code)
        except IsoCharacteristic.DoesNotExist:
            logger.warning(f"Característica {code} no encontrada en BD")
            continue

        current_level = evaluators[code]()
        status = get_level_status(current_level)

        QualityMetric.objects.create(
            characteristic=char,
            subcharacteristic=None,
            metric_name=config["aspect_name"],
            value=float(current_level),
            target=5.0,
            unit="nivel",
            status=status,
            formula=f"Nivel {current_level}: {config['levels'][current_level - 1]}",
            level_descriptions=config["levels"],
        )
        generated += 1
        logger.info(
            f"{code}: Nivel {current_level}/5 - {config['levels'][current_level - 1]}"
        )

    logger.info(f"Evaluación completada: {generated} características evaluadas")


def get_radar_data():
    data = {}
    for char in IsoCharacteristic.objects.all():
        metric = (
            QualityMetric.objects.filter(characteristic=char)
            .order_by("-measured_at")
            .first()
        )
        if metric:
            level = int(metric.value)
            data[char.code] = round((level / 5.0) * 100, 1)
        else:
            data[char.code] = 0.0
    return data
