# INFORME DE AUDITORÍA DE CALIDAD DE SOFTWARE

## SACAUDIT - Sistema de Auditoría para SACARF

---

**Universidad Nacional de Loja**
**Carrera de Ingeniería en Sistemas**
**Módulo: Procesos de Software**

---

## 1. Introducción

### 1.1. Contexto

El sistema **SACARF** (Sistema Automatizado de Control de Asistencia por Reconocimiento Facial) es una aplicación web full-stack desarrollada para la Universidad Nacional de Loja, que permite el registro de asistencia estudiantil mediante reconocimiento facial utilizando servicios AWS (Rekognition, S3, SES).

El presente informe documenta la implementación de **SACAUDIT**, un sistema externo e independiente de auditoría de calidad, alineado al modelo **ISO 25000 / ISO 25010** (SQuaRE), cuyo propósito es evaluar la calidad del producto software SACARF mediante la recolección de eventos, la evaluación por niveles de madurez (1-5) y la generación de informes auditables.

### 1.2. Objetivos

- Implementar un sistema independiente de auditoría de calidad para SACARF
- Evaluar 4 características clave del modelo ISO 25010 (Seguridad, Adecuación Funcional, Fiabilidad, Mantenibilidad) mediante niveles de madurez del 1 al 5
- Determinar el nivel de madurez de cada característica a partir de eventos reales recolectados vía API
- Producir informes PDF auditables con hallazgos y recomendaciones
- Proveer un dashboard visual para el monitoreo continuo de la calidad

### 1.3. Alcance

La auditoría evalúa **4 características de calidad** del modelo ISO 25010:

| Característica | Aspecto evaluado | Módulos de SACARF involucrados |
|---------------|-----------------|-------------------------------|
| **SEC** (Seguridad) | Protección contra ataques de fuerza bruta | Autenticación y control de acceso (login, logout, roles) |
| **FUN** (Adecuación Funcional) | Precisión del backend para rechazar registros inválidos | Registro de asistencia facial (captura con Rekognition), gestión de estudiantes, horarios y matrículas |
| **REL** (Fiabilidad) | Resiliencia ante interrupciones en servicios AWS | Registro de asistencia facial, disponibilidad del sistema |
| **MAI** (Mantenibilidad) | Aislamiento e impacto operativo al realizar cambios | Infraestructura Docker, documentación de la API (Swagger/ReDoc), estabilidad del sistema |

---

## 2. Marco Teórico: ISO 25000 / ISO 25010

### 2.1. Familia ISO 25000 (SQuaRE)

La familia **ISO 25000** — *Software engineering — Software product Quality Requirements and Evaluation (SQuaRE)* — es un conjunto de estándares internacionales para la evaluación de la calidad de productos de software. Reemplaza y unifica las anteriores normas ISO 9126 e ISO 14598.

### 2.2. Modelo de Calidad ISO 25010

La **ISO 25010** define un modelo de calidad de producto de software compuesto por **8 características principales**, cada una con sus respectivas subcaracterísticas:

| Código | Característica | Subcaracterísticas |
|--------|---------------|-------------------|
| **FUN** | Functional Suitability | Functional Completeness, Functional Correctness, Functional Appropriateness |
| **REL** | Reliability | Maturity, Availability, Fault Tolerance, Recoverability |
| **PER** | Performance Efficiency | Time Behavior, Resource Utilization, Capacity |
| **SEC** | Security | Confidentiality, Integrity, Non-repudiation, Accountability, Authenticity |
| **COM** | Compatibility | Co-existence, Interoperability |
| **USA** | Usability | Appropriateness Recognizability, Learnability, Operability, User Error Protection, Accessibility |
| **MAI** | Maintainability | Modularity, Reusability, Analyzability, Modifiability, Testability |
| **POR** | Portability | Adaptability, Installability, Replaceability |

> **Nota**: De las 8 características, SACAUDIT evalúa las 4 más relevantes para SACARF (SEC, FUN, REL, MAI) con escalas de madurez 1-5, dejando las restantes (PER, COM, USA, POR) como extensión futura.

---

## 3. Arquitectura del Sistema de Auditoría

### 3.1. Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SACAUDIT (Auditor)                           │
│                                                                     │
│  ┌─────────────────────┐    ┌──────────────────────────────────┐    │
│  │   Frontend Angular   │    │        Backend Django REST        │    │
│  │   (Dashboard 4300)   │◄──►│        (API:8000)                │    │
│  │                      │    │                                  │    │
│  │  ┌────────────────┐  │    │  ┌──────────┐ ┌──────────────┐  │    │
│  │  │ Dashboard      │  │    │  │ Collector │ │ Quality      │  │    │
│  │  │ Eventos        │  │    │  │ (Eventos) │ │ (ISO 25010)  │  │    │
│  │  │ Calidad        │  │    │  └─────┬────┘ └──────┬───────┘  │    │
│  │  │ Hallazgos      │  │    │        │             │          │    │
│  │  │ Informes       │  │    │  ┌─────▼─────────────▼───────┐  │    │
│  │  └────────────────┘  │    │  │    SQLite / PostgreSQL     │  │    │
│  └─────────────────────┘    │  └────────────────────────────┘  │    │
│                             └──────────────────────────────────┘    │
│                                        │                           │
│                             ┌──────────▼──────────┐                │
│                             │   Celery + Redis     │                │
│                             │   (Polling + Jobs)   │                │
│                             └──────────┬──────────┘                │
└────────────────────────────────────────┼───────────────────────────┘
                                         │ HTTP (Polling every 5-30 min)
                                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        SACARF (Auditado)                            │
│  API REST en http://localhost:8000/api/v1/                          │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2. Flujo de Datos

1. **Recolección**: Tareas Celery programadas consultan periódicamente los endpoints de SACARF (historial de asistencia, excepciones, estudiantes, disponibilidad, documentación)
2. **Almacenamiento**: Los eventos recolectados se persisten como `AuditEvent` en la base de datos del auditor
3. **Evaluación de niveles**: El motor `MetricsEngine` procesa los eventos y determina el nivel de madurez (1-5) para cada característica ISO 25010 evaluada
4. **Hallazgos**: Se registran hallazgos de auditoría (manuales y automáticos) clasificados como No Conformidades, Observaciones o Fortalezas
5. **Informes**: Se generan informes PDF con ReportLab incluyendo tablas de niveles de madurez, radar de calidad y hallazgos

### 3.3. Stack Tecnológico

| Componente | Tecnología |
|------------|-----------|
| Backend | Python 3.12, Django 4.2, Django REST Framework |
| Base de datos | SQLite (desarrollo), PostgreSQL (producción) |
| Tareas asíncronas | Celery 5.x + Redis |
| Frontend | Angular 17, Bootstrap 5, Bootstrap Icons |
| Informes PDF | ReportLab 5.x |
| Cliente HTTP | Requests (polling a SACARF) |

---

## 4. Características de Calidad Evaluadas — Niveles de Madurez

### 4.1. Escala de Madurez (1-5)

Cada característica se evalúa mediante un **nivel de madurez del 1 al 5**, donde:
- **Nivel 1**: Implementación mínima o inexistente
- **Nivel 2**: Implementación básica con deficiencias significativas
- **Nivel 3**: Implementación parcial, cumple requisitos mínimos
- **Nivel 4**: Implementación completa según lo esperado
- **Nivel 5**: Implementación óptima con valor añadido

### 4.2. Tabla de Niveles por Característica

#### Seguridad (SEC) — Protección contra ataques de fuerza bruta

| Nivel | Descripción |
|-------|-------------|
| 1 | No bloquea cuenta, no expira JWT, permite intentos infinitos de sesión |
| 2 | El token JWT expira, pero el contador de intentos fallidos no bloquea al usuario |
| 3 | Bloquea la cuenta tras 5 intentos fallidos, pero sin contador regresivo |
| 4 | Token JWT expira en 15 minutos y tras 5 intentos fallidos la cuenta se bloquea con contador regresivo |
| 5 | Nivel 4, además notifica administrativamente el bloqueo y registra la IP del intento fallido |

#### Adecuación Funcional (FUN) — Precisión del backend para rechazar registros inválidos

| Nivel | Descripción |
|-------|-------------|
| 1 | Permite registrar asistencia de cualquier estudiante en cualquier curso sin validar matrícula |
| 2 | Valida al estudiante, pero permite registrar asistencia en asignaturas donde no está matriculado |
| 3 | Valida la matrícula, pero permite registrar asistencia fuera del horario activo de la clase |
| 4 | El endpoint verifica que el alumno esté matriculado en el curso y en el horario activo |
| 5 | Nivel 4, y la validación se ejecuta en menos de 100ms |

#### Fiabilidad (REL) — Resiliencia ante interrupciones en servicios AWS

| Nivel | Descripción |
|-------|-------------|
| 1 | Si AWS Rekognition falla o da timeout, la aplicación colapsa, interrumpe el flujo y pierde datos |
| 2 | Captura el fallo, pero muestra error genérico al usuario y obliga a repetir manualmente desde cero |
| 3 | No colapsa, pero deja la asistencia registrada como "Falta" sin opción a recuperar la imagen |
| 4 | Captura la excepción, encola la imagen de forma asíncrona en S3 con estado "Pendiente" y reintenta automáticamente |
| 5 | Nivel 4, y el reintento se completa de forma transparente para el usuario en menos de 3 intentos |

#### Mantenibilidad (MAI) — Aislamiento e impacto operativo al realizar cambios

| Nivel | Descripción |
|-------|-------------|
| 1 | Componentes acoplados: un cambio en código rompe la BD o requiere recompilación Angular |
| 2 | Usa contenedores Docker, pero comparten almacenamiento interno o variables hardcodeadas |
| 3 | Servicios separados en Docker, pero actualizar el contenedor del backend genera caídas prolongadas |
| 4 | Servicios independientes en Docker Compose con variables en archivo .env |
| 5 | Desacoplamiento total: contenedores se destruyen y recrean instantáneamente con downtime mínimo |

### 4.3. Determinación del Nivel

El nivel de madurez se determina automáticamente mediante el motor de métricas `MetricsEngine`, que analiza los eventos recolectados vía polling de la API de SACARF. La evaluación considera:

- **Seguridad**: Patrones de inicio de sesión exitosos y fallidos, detección de bloqueo por intentos
- **Funcional**: Registros de asistencia recolectados, validación de matrículas y horarios
- **Fiabilidad**: Disponibilidad del sistema, tasa de errores, patrones de fallo y recuperación
- **Mantenibilidad**: Estabilidad de la API, disponibilidad continua, documentación accesible

### 4.4. Cálculo del Puntaje Global

El puntaje global de calidad se calcula como el promedio de los niveles de madurez convertido a porcentaje:

```
Puntaje_Global = (Σ(Nivel_Característica_i) / (N × 5)) × 100

donde:
  N = número de características evaluadas (4: SEC, FUN, REL, MAI)
  Nivel_Característica_i = nivel actual (1-5) de la característica i
```

---

## 5. Modelo de Datos

### 5.1. Auditor - AuditEvent

```python
class AuditEvent(models.Model):
    event_type    # LOGIN, CAPTURE, EXCEPTION, SYSTEM_AVAILABLE, etc.
    source        # "SACARF"
    user_email    # Email del usuario que realizó la acción
    user_role     # ADMIN, TEACHER, STUDENT
    action        # Descripción de la acción
    entity_type   # "User", "Student", "AttendanceRecord", etc.
    entity_id     # ID de la entidad afectada
    old_value     # JSON - valor anterior (para trazabilidad)
    new_value     # JSON - valor nuevo
    ip_address    # Dirección IP origen
    timestamp     # Fecha del evento original
    collected_at  # Fecha de recolección por el auditor
```

### 5.2. Auditor - QualityMetric

```python
class QualityMetric(models.Model):
    characteristic      # FK → IsoCharacteristic (FUN, REL, SEC...)
    subcharacteristic   # FK → IsoSubcharacteristic (opcional)
    metric_name         # Aspecto evaluado (ej: "Protección contra fuerza bruta")
    value               # Nivel actual (1-5)
    target              # Nivel máximo (siempre 5)
    unit                # Unidad: "nivel"
    status              # COMPLIANT / WARNING / NON_COMPLIANT / NOT_MEASURED
    formula             # Descripción del nivel actual
    level_descriptions  # JSON - Lista de descriptores para cada nivel (1-5)
    measured_at         # Fecha de la medición
```

### 5.3. Auditor - AuditFinding

```python
class AuditFinding(models.Model):
    finding_type       # NC (No Conformidad), OBS (Observación), STR (Fortaleza)
    characteristic     # FK → IsoCharacteristic
    severity           # CRITICAL, MAJOR, MINOR
    description        # Descripción del hallazgo
    evidence           # JSON - evidencia asociada
    status             # OPEN, IN_PROGRESS, CLOSED
    corrective_action  # Acción correctiva propuesta
    created_at         # Fecha de creación
    resolved_at        # Fecha de resolución
```

---

## 6. Implementación

### 6.1. Estructura del Proyecto

```
audit-system/
├── backend/                          # Django REST API
│   ├── manage.py
│   ├── requirements.txt
│   ├── config/
│   │   ├── settings.py
│   │   ├── urls.py                   # Rutas globales (/api/...)
│   │   ├── wsgi.py
│   │   └── celery.py                 # Configuración Celery
│   └── apps/
│       ├── collector/                # Recolección de eventos
│       │   ├── models.py             # AuditEvent
│       │   ├── serializers.py
│       │   ├── views.py              # /api/events/ + /api/events/stats/
│       │   ├── sacarf_client.py      # Cliente HTTP para API de SACARF
│       │   └── tasks.py              # Tareas Celery de polling
│       ├── quality/                  # Niveles de madurez ISO 25010
│       │   ├── models.py             # IsoCharacteristic, QualityMetric (con level_descriptions), AuditFinding
│       │   ├── serializers.py
│       │   ├── views.py              # /api/quality/...
│       │   ├── metrics_engine.py     # Evaluación de niveles de madurez 1-5
│       │   ├── tasks.py              # Recalcular métricas periódicamente
│       │   └── management/commands/
│       │       └── seed_iso25010.py  # Datos iniciales ISO 25010
│       └── reports/                  # Informes PDF
│           ├── models.py             # AuditReport
│           ├── serializers.py
│           ├── views.py              # /api/reports/...
│           ├── pdf_generator.py      # Generación PDF con ReportLab
│           └── tasks.py              # Generación automática
├── frontend/                         # Dashboard Angular
│   ├── angular.json
│   ├── package.json
│   └── src/
│       ├── index.html
│       ├── main.ts
│       ├── styles.scss
│       └── app/
│           ├── app.module.ts
│           ├── app-routing.module.ts
│           ├── app.component.ts      # Layout con sidebar
│           ├── core/
│           │   ├── models/
│           │   │   └── audit.models.ts
│           │   └── services/
│           │       ├── audit-event.service.ts
│           │       ├── quality.service.ts
│           │       └── report.service.ts
│           └── features/
│               ├── dashboard/        # Radar ISO 25010 + KPIs
│               ├── events/           # Tabla de eventos + detalle
│               ├── quality/          # Métricas por característica
│               ├── findings/         # CRUD de hallazgos
│               └── reports/          # Generación y descarga de PDF
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── docker-compose.yml
│   ├── nginx.conf
│   └── entrypoint.sh
└── docs/
    └── informe-auditoria-sacaudit.md  # Este documento
```

### 6.2. API Endpoints

#### Recolección de Eventos

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/api/events/` | Lista paginada de eventos auditados (filtros: event_type, user_email, date) |
| `GET` | `/api/events/stats/` | Estadísticas: totales, por tipo, por usuario |
| `GET` | `/api/events/{id}/` | Detalle completo de un evento (incluye old/new values) |

#### Calidad ISO 25010

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/api/quality/characteristics/` | Catálogo de 8 características ISO 25010 con subcaracterísticas |
| `GET` | `/api/quality/metrics/` | Niveles de madurez calculados (filtrables por característica) |
| `GET` | `/api/quality/metrics/latest/` | Últimos niveles por característica |
| `GET` | `/api/quality/metrics/levels/` | Niveles de madurez (SEC, FUN, REL, MAI) con descriptores |
| `GET` | `/api/quality/dashboard/summary/` | Resumen para el dashboard (radar + niveles + KPIs + últimos eventos) |
| `GET` | `/api/quality/findings/` | Lista de hallazgos de auditoría |
| `POST` | `/api/quality/findings/` | Crear hallazgo manual |
| `PATCH` | `/api/quality/findings/{id}/` | Actualizar hallazgo (estado, acción correctiva) |
| `GET` | `/api/quality/findings/stats/` | Estadísticas de hallazgos |

#### Informes PDF

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/api/reports/` | Historial de informes generados |
| `POST` | `/api/reports/generate/` | Generar nuevo informe (body: period_start, period_end, title) |
| `GET` | `/api/reports/{id}/download/` | Descargar PDF del informe |

### 6.3. Tareas Programadas (Celery Beat)

| Tarea | Descripción | Frecuencia |
|-------|-------------|------------|
| `check_system_availability` | Verifica disponibilidad de SACARF | Cada 5 minutos |
| `collect_attendance_history` | Recolecta registros de asistencia | Cada 30 minutos |
| `collect_exceptions` | Recolecta justificaciones | Cada 30 minutos |
| `collect_students` | Verifica estudiantes activos | Cada 1 hora |
| `check_api_documentation` | Verifica Swagger | Cada 24 horas |
| `test_authentication` | Prueba de autenticación | Cada 1 hora |
| `recalculate_metrics` | Reevalúa niveles de madurez (1-5) de SEC, FUN, REL, MAI | Cada 1 hora |
| `generate_auto_report` | Genera informe PDF automático | Cada 24 horas (medianoche) |

### 6.4. Dashboard Angular

El frontend consta de 5 vistas principales:

| Ruta | Componente | Contenido |
|------|-----------|-----------|
| `/dashboard` | DashboardComponent | Radar chart con puntajes por característica, tarjetas KPI (puntaje global, eventos totales, hallazgos abiertos, características en nivel conforme (≥ 4)), últimos 10 eventos |
| `/events` | EventListComponent | Tabla paginada y filtrable (tipo, usuario, rango de fechas), acciones de detalle |
| `/events/:id` | EventDetailComponent | Vista detalle con old/new values en formato JSON |
| `/quality` | QualityMetricsComponent | Tarjetas por cada nivel de madurez (SEC, FUN, REL, MAI) con barra de progreso 1-5, descriptor actual y lista de todos los niveles |
| `/findings` | FindingsComponent | Tabla de hallazgos + formulario modal para crear/editar, botón de cierre |
| `/reports` | ReportsComponent | Historial de informes + formulario modal para generar nuevo + descarga PDF |

---

## 7. Tabla de Aspectos de Calidad Implementados

| # | Aspecto de Calidad | Implementación en SACAUDIT | Artefacto |
|---|-------------------|--------------------------|-----------|
| 1 | **Trazabilidad completa** | Cada `AuditEvent` registra usuario, acción, entidad, valores anterior/nuevo, IP y timestamp | `AuditEvent` model |
| 2 | **Independencia del auditor** | Sistema externo separado de SACARF, sin modificar su código fuente | Proyecto `audit-system/` |
| 3 | **Cobertura ISO 25010** | 4 características evaluadas (SEC, FUN, REL, MAI) con niveles 1-5; las 8 características y 27 subcaracterísticas modeladas en BD | `IsoCharacteristic`, `IsoSubcharacteristic` |
| 4 | **Niveles de madurez (1-5)** | Evaluación por niveles de madurez con descriptores por nivel, calculados desde eventos reales | `QualityMetric` + `MetricsEngine` |
| 5 | **Hallazgos clasificados** | No Conformidades, Observaciones y Fortalezas con severidad y estado | `AuditFinding` model |
| 6 | **Informes auditables** | PDF con estructura formal (introducción, métricas, hallazgos, conclusiones) | `AuditReportPDF` (ReportLab) |
| 7 | **Monitoreo continuo** | Tareas Celery programadas recolectan datos periódicamente | `collector/tasks.py` |
| 8 | **Dashboard visual** | Interfaz web con radar chart, KPIs, tablas filtrables | Frontend Angular |
| 9 | **Evidencia almacenada** | Respuestas originales de API preservadas como `raw_response` | `AuditEvent.raw_response` |
| 10 | **Generación automática** | Informes PDF generados sin intervención manual cada 24h | `reports/tasks.py` |

---

## 8. Resultados Esperados

### 8.1. Dashboard

El dashboard de SACAUDIT permite visualizar:

- **Radar Chart ISO 25010**: Puntaje porcentual convertido desde nivel de madurez en cada característica
- **KPIs principales**: Puntaje global, total de eventos auditados, hallazgos abiertos, características en nivel conforme (≥ 4)
- **Tabla de niveles de madurez**: Las 4 características evaluadas (SEC, FUN, REL, MAI) con su nivel 1-5, descriptor actual y estado (cumple/observación/no cumple)
- **Últimos eventos**: Lista en tiempo real de los eventos más recientes recolectados de SACARF

### 8.2. Informe PDF

Cada informe generado incluye:

1. Portada con datos del período y tipo de informe
2. Introducción con objetivo y alcance de la auditoría
3. Tabla de niveles de madurez ISO 25010 con código, aspecto evaluado, nivel (1-5) y estado
4. Tabla detallada con descriptores de todos los niveles por característica
5. Lista de hallazgos con tipo, severidad, descripción y estado
6. Resumen de eventos auditados por tipo
7. Conclusiones y recomendaciones

### 8.3. Hallazgos

Los hallazgos se clasifican en:

- **No Conformidad (NC)**: Incumplimiento de un requisito especificado (ej: nivel de madurez ≤ 2 en alguna característica)
- **Observación (OBS)**: Área de mejora potencial (ej: nivel de madurez = 3, puede mejorarse)
- **Fortaleza (STR)**: Aspecto destacable del sistema (ej: nivel de madurez ≥ 4 en alguna característica)

---

## 9. Guía de Instalación y Ejecución

### 9.1. Requisitos

- Python 3.12+
- Node.js 20+
- Redis (para Celery)

### 9.2. Instalación Local

```bash
# 1. Backend
cd audit-system/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Migraciones y datos iniciales
python manage.py migrate
python manage.py seed_iso25010

# 3. Iniciar servidor
python manage.py runserver 0.0.0.0:8000

# 4. Celery (en otra terminal)
celery -A config worker --loglevel=info
celery -A config beat --loglevel=info

# 5. Frontend
cd ../frontend
npm install
npm start  # Disponible en http://localhost:4300
```

### 9.3. Ejecución con Docker

```bash
cd audit-system
docker-compose -f docker/docker-compose.yml up --build
```

Servicios:
| Servicio | Puerto | URL |
|----------|--------|-----|
| Frontend | 4300 | http://localhost:4300 |
| API | 8001 | http://localhost:8001/api/ |

---

## 10. Conclusiones

1. **SACAUDIT** demuestra la aplicabilidad del modelo ISO 25010 para la evaluación objetiva de la calidad, aplicando niveles de madurez (1-5) con descriptores textuales específicos en 4 características (SEC, FUN, REL, MAI) sobre SACARF.

2. La arquitectura de sistema externo independiente garantiza la imparcialidad de la auditoría y no interfiere con la operación del sistema auditado.

3. El uso de polling periódico con Celery permite un monitoreo continuo sin requerir modificaciones en el sistema auditado.

4. La generación de informes PDF estructurados con niveles de madurez proporciona evidencia documentada para procesos de certificación de calidad.

5. El dashboard visual facilita la interpretación de los niveles de madurez de calidad por parte de los stakeholders no técnicos.

## 11. Recomendaciones

1. Implementar mecanismos de webhook en SACARF para notificación en tiempo real de eventos críticos, mejorando la capacidad de respuesta del auditor.

2. Extender la evaluación por niveles de madurez a las características restantes (PER, COM, USA, POR) con escalas 1-5 y descriptores propios.

3. Integrar pruebas automatizadas de rendimiento (Performance Efficiency) como evidencia para alcanzar nivel 5 en Adecuación Funcional.

4. Incorporar análisis de tendencias históricas de los niveles de madurez para detectar degradación progresiva de la calidad.

---

*Documento generado como parte del proyecto académico de la Universidad Nacional de Loja (UNL).*
*SACAUDIT v1.0 — Junio 2026*
