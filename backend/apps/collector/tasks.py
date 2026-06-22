import logging
from celery import shared_task
from django.utils import timezone
from .sacarf_client import SacarfClient
from .models import AuditEvent

logger = logging.getLogger(__name__)


def create_event(event_type, action, data=None, user_email=None, user_role=None):
    AuditEvent.objects.create(
        event_type=event_type,
        action=action,
        source="SACARF",
        user_email=user_email,
        user_role=user_role,
        entity_type=data.get("entity_type", "") if data else "",
        entity_id=data.get("entity_id", "") if data else "",
        old_value=data.get("old_value") if data else None,
        new_value=data.get("new_value") if data else None,
        ip_address=data.get("ip_address") if data else None,
        timestamp=timezone.now(),
        raw_response=data,
    )


@shared_task
def check_system_availability():
    client = SacarfClient()
    available, response_data = client.check_availability()
    event_type = "SYSTEM_AVAILABLE" if available else "SYSTEM_UNAVAILABLE"
    action = "Verificación de disponibilidad del sistema"
    create_event(event_type, action, response_data)
    logger.info(f"Disponibilidad SACARF: {'OK' if available else 'FALLO'}")
    return available


@shared_task
def collect_attendance_history():
    client = SacarfClient()
    page = 1
    count = 0
    while True:
        data = client.get_attendance_history(page=page)
        if not data or not data.get("results"):
            break
        for record in data["results"]:
            create_event(
                "CAPTURE",
                "Captura de asistencia facial",
                record,
                user_email=record.get("student", {}).get("user_email"),
                user_role="STUDENT",
            )
            count += 1
        if not data.get("next"):
            break
        page += 1
    logger.info(f"Recolectados {count} registros de asistencia")
    return count


@shared_task
def collect_exceptions():
    client = SacarfClient()
    page = 1
    count = 0
    while True:
        data = client.get_exceptions(page=page)
        if not data or not data.get("results"):
            break
        for exc in data["results"]:
            create_event(
                "EXCEPTION",
                "Justificación de inasistencia",
                exc,
                user_email=exc.get("modified_by_email"),
                user_role="TEACHER",
            )
            count += 1
        if not data.get("next"):
            break
        page += 1
    logger.info(f"Recolectadas {count} excepciones")
    return count


@shared_task
def collect_students():
    client = SacarfClient()
    page = 1
    count = 0
    while True:
        data = client.get_students(page=page)
        if not data or not data.get("results"):
            break
        for student in data["results"]:
            create_event(
                "STUDENT_CREATE",
                "Verificación de estudiante activo",
                student,
                user_email=student.get("user_email"),
                user_role="STUDENT",
            )
            count += 1
        if not data.get("next"):
            break
        page += 1
    logger.info(f"Verificados {count} estudiantes")
    return count


@shared_task
def check_api_documentation():
    client = SacarfClient()
    available = client.get_swagger_docs()
    event_type = "API_DOCS_OK" if available else "API_DOCS_FAIL"
    action = "Verificación de documentación API"
    create_event(event_type, action, {"available": available})
    logger.info(f"Documentación API: {'OK' if available else 'FALLO'}")
    return available


@shared_task
def test_authentication():
    client = SacarfClient()
    status_code, data = client.test_login()
    if status_code == 200:
        create_event(
            "LOGIN",
            "Prueba de autenticación exitosa",
            {"status_code": status_code},
        )
        return True
    else:
        create_event(
            "LOGIN_FAILED",
            "Prueba de autenticación fallida",
            {"status_code": status_code},
        )
        return False
