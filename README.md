# SACAUDIT — Sistema de Auditoría de Calidad ISO 25010

Sistema externo e independiente que audita la calidad del sistema **SACARF** mediante la recolección de eventos, evaluación por **niveles de madurez (1-5)** en 4 características ISO 25010 (Seguridad, Funcionalidad, Fiabilidad, Mantenibilidad), dashboards en **Grafana** e informes PDF.

## Requisitos

| Componente | Versión |
|-----------|---------|
| Python | 3.12+ |
| Docker | 24+ (para Grafana) |
| Redis | 7+ (en Docker o local) |

## Inicio rápido

```bash
# 1. Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Migraciones y datos iniciales
python manage.py migrate
python manage.py seed_iso25010

# 3. Iniciar backend
python manage.py runserver 0.0.0.0:8001 &

# 4. Celery
celery -A config worker --loglevel=info &
celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler &

# 5. Redis (Docker)
docker run -d --name sacaudit-redis -p 6379:6379 redis:7-alpine

# 6. Grafana (Docker)
chcon -Rt svirt_sandbox_file_t ../docker/grafana/provisioning/ 2>/dev/null || true
docker run -d --name sacaudit-grafana \
  --add-host host.docker.internal:host-gateway \
  -p 3000:3000 \
  -e GF_INSTALL_PLUGINS=yesoreyeram-infinity-datasource \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  -v $(pwd)/../docker/grafana/provisioning:/etc/grafana/provisioning \
  grafana/grafana:latest
```

## Arquitectura

```
                    ┌──────────────────────────────────────┐
                    │           SACAUDIT                    │
                    │                                      │
                    │  ┌─────────┐    ┌─────────────────┐  │
                    │  │ Grafana │◄──►│  Django REST API │  │
                    │  │ :3000   │    │  :8001           │  │
                    │  └─────────┘    └────────┬────────┘  │
                    │                          │            │
                    │              ┌───────────▼────────┐   │
                    │              │  Celery + Redis     │   │
                    │              └───────────┬────────┘   │
                    └──────────────────────────┼────────────┘
                                               │ HTTP Polling
                                               ▼
                    ┌──────────────────────────────────────┐
                    │      SACARF (Sistema Auditado)        │
                    │      http://localhost:8000/api/v1      │
                    └──────────────────────────────────────┘
```

## Servicios

| Servicio | Puerto | URL | Credenciales |
|----------|--------|-----|-------------|
| **Grafana** | 3000 | http://localhost:3000 | `admin` / `admin` |
| **API Django** | 8001 | http://localhost:8001/api/ | — |
| **Admin Django** | 8001 | http://localhost:8001/admin/ | crear superusuario |
| **Redis** | 6379 | — | — |

## API Endpoints

| Recurso | Endpoints |
|---------|-----------|
| **Eventos** | `GET /api/events/` `GET /api/events/{id}/` `GET /api/events/stats/` |
| **Características** | `GET /api/quality/characteristics/` |
| **Niveles de madurez** | `GET /api/quality/metrics/` `GET /api/quality/metrics/latest/` `GET /api/quality/metrics/levels/` `GET /api/quality/metrics/history/` `GET /api/quality/dashboard/summary/` |
| **Hallazgos** | `GET/POST /api/quality/findings/` `PATCH /api/quality/findings/{id}/` `GET /api/quality/findings/stats/` |
| **Informes** | `GET /api/reports/` `POST /api/reports/generate/` `GET /api/reports/{id}/download/` |

## Dashboard Grafana

Acceder a http://localhost:3000 con `admin`/`admin`.

Paneles incluidos:
- **KPIs**: Puntaje global, eventos auditados, hallazgos abiertos, características conformes
- **Niveles de madurez**: Barra horizontal 1-5 por característica + tabla con descriptores
- **Eventos**: Tabla con últimos 20 eventos recolectados
- **Hallazgos**: Tabla completa + contadores por tipo (NC/OBS/STR)

Hallazgos CRUD: http://localhost:8001/admin/

## Niveles de Madurez (1-5)

| Característica | Aspecto evaluado |
|---------------|-----------------|
| **SEC** | Protección contra fuerza bruta en login |
| **FUN** | Validación de matrícula y horario en registro facial |
| **REL** | Resiliencia ante fallos de AWS Rekognition |
| **MAI** | Desacoplamiento Docker y configuración |

## Tareas Programadas

| Tarea | Frecuencia |
|-------|-----------|
| `check_system_availability` | Cada 5 min |
| `collect_attendance_history` | Cada 30 min |
| `collect_exceptions` | Cada 30 min |
| `test_authentication` | Cada 1 h |
| `recalculate_metrics` | Cada 1 h |
| `generate_auto_report` | Cada 24 h |

## Solución de problemas

**SELinux**: En Fedora/RHEL/CentOS, ejecutar:
```bash
chcon -Rt svirt_sandbox_file_t docker/grafana/provisioning/
```

**Redis no disponible**: Verificar que el contenedor Redis corre:
```bash
docker ps | grep sacaudit-redis
docker exec sacaudit-redis redis-cli ping  # debe responder PONG
```
