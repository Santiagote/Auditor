import io
import os
from datetime import date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, ListFlowable, ListItem,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from django.conf import settings
from apps.quality.models import AuditFinding, QualityMetric, IsoCharacteristic
from apps.collector.models import AuditEvent
from apps.reports.models import AuditReport
from django.utils import timezone


class AuditReportPDF:

    def __init__(self, report):
        self.report = report
        self.buffer = io.BytesIO()
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        self.styles.add(ParagraphStyle(
            "TitleUNL",
            parent=self.styles["Title"],
            fontSize=18,
            spaceAfter=6,
            textColor=colors.HexColor("#1a4d2e"),
        ))
        self.styles.add(ParagraphStyle(
            "SubTitle",
            parent=self.styles["Normal"],
            fontSize=12,
            spaceAfter=20,
            textColor=colors.HexColor("#555555"),
            alignment=TA_CENTER,
        ))
        self.styles.add(ParagraphStyle(
            "SectionHeader",
            parent=self.styles["Heading2"],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor("#1a4d2e"),
            borderWidth=1,
            borderColor=colors.HexColor("#1a4d2e"),
            borderPadding=4,
        ))
        self.styles.add(ParagraphStyle(
            "TableCell",
            parent=self.styles["Normal"],
            fontSize=8,
            leading=10,
        ))
        self.styles.add(ParagraphStyle(
            "FindingItem",
            parent=self.styles["Normal"],
            fontSize=9,
            leading=13,
            leftIndent=10,
            spaceAfter=4,
        ))

    def _header_footer(self, canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#888888"))
        canvas.drawString(20 * mm, 10 * mm, "SACAUDIT - Sistema de Auditoría de Calidad")
        canvas.drawRightString(
            A4[0] - 20 * mm, 10 * mm,
            f"Página {doc.page}"
        )
        canvas.restoreState()

    def build(self):
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
        )

        elements = []
        elements.extend(self._build_cover())
        elements.append(PageBreak())
        elements.extend(self._build_introduction())
        elements.append(PageBreak())
        elements.extend(self._build_quality_characteristics())
        elements.append(PageBreak())
        elements.extend(self._build_metrics_table())
        elements.append(PageBreak())
        elements.extend(self._build_findings())
        elements.append(PageBreak())
        elements.extend(self._build_events_summary())
        elements.append(PageBreak())
        elements.extend(self._build_conclusions())

        doc.build(elements, onFirstPage=self._header_footer,
                  onLaterPages=self._header_footer)
        return self.buffer

    def _build_cover(self):
        elements = []
        elements.append(Spacer(1, 60 * mm))
        elements.append(Paragraph(
            "SACAUDIT", self.styles["TitleUNL"]
        ))
        elements.append(Paragraph(
            "Sistema de Auditoría de Calidad de Software",
            self.styles["SubTitle"],
        ))
        elements.append(Spacer(1, 15 * mm))
        elements.append(Paragraph(
            f"<b>Informe de Auditoría</b>", self.styles["Normal"]
        ))
        elements.append(Spacer(1, 5 * mm))
        elements.append(Paragraph(
            f"<b>Período:</b> {self.report.period_start} al {self.report.period_end}",
            self.styles["Normal"],
        ))
        elements.append(Paragraph(
            f"<b>Generado:</b> {self.report.generated_at.strftime('%d/%m/%Y %H:%M')}",
            self.styles["Normal"],
        ))
        elements.append(Paragraph(
            f"<b>Tipo:</b> {dict(AuditReport.ReportType.choices).get(self.report.report_type, 'Manual')}",
            self.styles["Normal"],
        ))
        elements.append(Spacer(1, 10 * mm))
        elements.append(Paragraph(
            "Universidad Nacional de Loja",
            ParagraphStyle("Footer", parent=self.styles["Normal"],
                           alignment=TA_CENTER, fontSize=10,
                           textColor=colors.HexColor("#888888")),
        ))
        return elements

    def _build_introduction(self):
        elements = []
        elements.append(Paragraph("1. Introducción", self.styles["SectionHeader"]))
        elements.append(Paragraph(
            "El presente informe presenta los resultados de la auditoría de calidad "
            "realizada al sistema <b>SACARF</b> (Sistema Automatizado de Control de Asistencia "
            "por Reconocimiento Facial), desarrollado para la Universidad Nacional de Loja.",
            self.styles["Normal"],
        ))
        elements.append(Spacer(1, 5 * mm))
        elements.append(Paragraph(
            "La auditoría se ha realizado bajo el marco del modelo <b>ISO 25000 / ISO 25010</b> "
            "(SQuaRE - Software Quality Requirements and Evaluation), evaluando las 8 "
            "características principales de calidad de producto de software.",
            self.styles["Normal"],
        ))
        elements.append(Spacer(1, 5 * mm))
        elements.append(Paragraph(
            "<b>Objetivo:</b> Evaluar la calidad del software SACARF mediante el monitoreo "
            "continuo de eventos y métricas, identificando no conformidades, observaciones "
            "y fortalezas del sistema.",
            self.styles["Normal"],
        ))
        elements.append(Spacer(1, 5 * mm))
        elements.append(Paragraph(
            "<b>Alcance:</b> El sistema auditor SACAUDIT recolecta eventos vía API REST "
            "de SACARF, calcula métricas de calidad y genera hallazgos de auditoría "
            "de forma automática y manual.",
            self.styles["Normal"],
        ))
        return elements

    def _build_quality_characteristics(self):
        elements = []
        elements.append(Paragraph("2. Niveles de Madurez ISO 25010", self.styles["SectionHeader"]))
        elements.append(Paragraph(
            "El modelo ISO 25010 define 8 características de calidad de producto de software. "
            "A continuación se presentan los niveles de madurez (1-5) evaluados "
            "para las características auditadas de SACARF:",
            self.styles["Normal"],
        ))
        elements.append(Spacer(1, 5 * mm))

        level_names = [
            "Protección contra ataques de fuerza bruta",
            "Precisión del backend para rechazar registros inválidos",
            "Resiliencia ante interrupciones en servicios AWS",
            "Aislamiento e impacto operativo al realizar cambios",
        ]
        metrics = QualityMetric.objects.select_related("characteristic").filter(
            metric_name__in=level_names
        ).order_by("characteristic__code")

        data = [["Código", "Característica", "Aspecto", "Nivel", "Estado"]]
        score_sum = 0
        count = 0
        for m in metrics:
            level = int(m.value)
            score_sum += level
            count += 1
            status_icon = {
                "COMPLIANT": "🟢",
                "WARNING": "🟡",
                "NON_COMPLIANT": "🔴",
            }.get(m.status, "⚪")
            level_bar = "■" * level + "□" * (5 - level)
            data.append([
                m.characteristic.code,
                m.characteristic.name,
                m.metric_name,
                f"{level_bar} ({level}/5)",
                f"{status_icon} {dict(m.Status.choices).get(m.status, '')}",
            ])

        if count > 0:
            global_score = round((score_sum / (count * 5)) * 100, 1)
            data.append(["", "", "PUNTAJE GLOBAL", f"{global_score}%", ""])

        col_widths = [20 * mm, 45 * mm, 50 * mm, 30 * mm, 25 * mm]
        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a4d2e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (3, 1), (4, -1), "CENTER"),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e8f5e9")),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)

        if count > 0 and global_score >= 70:
            elements.append(Paragraph(
                "El sistema presenta un nivel de madurez ACEPTABLE.",
                self.styles["Normal"],
            ))
        elif count > 0 and global_score >= 40:
            elements.append(Paragraph(
                "El sistema presenta un nivel de madurez REGULAR, se requieren mejoras.",
                self.styles["Normal"],
            ))
        elif count > 0:
            elements.append(Paragraph(
                "El sistema presenta un nivel de madurez INSUFICIENTE, "
                "se requieren acciones correctivas urgentes.",
                self.styles["Normal"],
            ))

        return elements

    def _build_metrics_table(self):
        elements = []
        elements.append(Paragraph("3. Tabla Detallada de Niveles de Madurez", self.styles["SectionHeader"]))
        elements.append(Paragraph(
            "A continuación se presentan los descriptores detallados para cada nivel "
            "de madurez evaluado en las características de SACARF:",
            self.styles["Normal"],
        ))
        elements.append(Spacer(1, 5 * mm))

        level_names = [
            "Protección contra ataques de fuerza bruta",
            "Precisión del backend para rechazar registros inválidos",
            "Resiliencia ante interrupciones en servicios AWS",
            "Aislamiento e impacto operativo al realizar cambios",
        ]
        metrics = QualityMetric.objects.filter(
            metric_name__in=level_names
        ).order_by("characteristic__code")

        data = [["Código", "Aspecto", "Nivel", "Descripción del Nivel"]]
        for m in metrics:
            level = int(m.value)
            level_desc = ""
            if m.level_descriptions and len(m.level_descriptions) >= level:
                level_desc = m.level_descriptions[level - 1]
            data.append([
                m.characteristic.code,
                m.metric_name,
                f"{level}/5",
                level_desc,
            ])
            if m.level_descriptions:
                for i, desc in enumerate(m.level_descriptions):
                    if i + 1 != level:
                        data.append(["", f"  Nivel {i+1}", "", desc])

        col_widths = [18 * mm, 38 * mm, 15 * mm, 95 * mm]
        table = Table(data, colWidths=col_widths, repeatRows=1)
        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a4d2e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("ALIGN", (2, 1), (2, -1), "CENTER"),
            ("ALIGN", (0, 1), (0, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#f5f5f5")]),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]
        row_idx = 1
        for m in metrics:
            style_cmds.append(
                ("BACKGROUND", (0, row_idx), (-1, row_idx), colors.HexColor("#e8f5e9"))
            )
            style_cmds.append(
                ("FONTNAME", (0, row_idx), (-1, row_idx), "Helvetica-Bold")
            )
            row_idx += 1
            if m.level_descriptions:
                row_idx += len(m.level_descriptions) - 1

        table.setStyle(TableStyle(style_cmds))
        elements.append(table)
        return elements

    def _build_findings(self):
        elements = []
        elements.append(Paragraph("4. Hallazgos de Auditoría", self.styles["SectionHeader"]))
        elements.append(Paragraph(
            "Los hallazgos se clasifican en No Conformidades (NC), Observaciones (OBS) "
            "y Fortalezas (STR), con su respectiva severidad y estado actual:",
            self.styles["Normal"],
        ))
        elements.append(Spacer(1, 5 * mm))

        findings = AuditFinding.objects.select_related("characteristic").all()

        if not findings:
            elements.append(Paragraph(
                "<i>No se registraron hallazgos en este período.</i>",
                self.styles["Normal"],
            ))
            return elements

        data = [["Tipo", "Severidad", "Descripción", "Característica", "Estado"]]
        for f in findings:
            type_icon = {"NC": "🔴", "OBS": "🟡", "STR": "🟢"}.get(f.finding_type, "⚪")
            severity_colors = {"CRITICAL": "Crítico", "MAJOR": "Mayor", "MINOR": "Menor"}
            data.append([
                f"{type_icon} {dict(f.FindingType.choices).get(f.finding_type, '')}",
                severity_colors.get(f.severity, f.severity),
                f.description[:80] + ("..." if len(f.description) > 80 else ""),
                f.characteristic.code if f.characteristic else "-",
                dict(f.FindingStatus.choices).get(f.status, f.status),
            ])

        col_widths = [30 * mm, 20 * mm, 60 * mm, 25 * mm, 20 * mm]
        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a4d2e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#f5f5f5")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(table)

        summary = self.report.findings_summary or {}
        if summary:
            elements.append(Spacer(1, 5 * mm))
            elements.append(Paragraph(
                "<b>Resumen:</b> "
                f"NC: {summary.get('NC', 0)}, "
                f"OBS: {summary.get('OBS', 0)}, "
                f"STR: {summary.get('STR', 0)}",
                self.styles["Normal"],
            ))

        return elements

    def _build_events_summary(self):
        elements = []
        elements.append(Paragraph("5. Resumen de Eventos Auditados", self.styles["SectionHeader"]))
        elements.append(Paragraph(
            "El sistema auditor ha recolectado los siguientes eventos desde SACARF "
            "durante el período evaluado:",
            self.styles["Normal"],
        ))
        elements.append(Spacer(1, 5 * mm))

        period_events = AuditEvent.objects.filter(
            timestamp__date__gte=self.report.period_start,
            timestamp__date__lte=self.report.period_end,
        )
        total = period_events.count()

        from django.db.models import Count
        by_type = dict(
            period_events.values("event_type")
            .annotate(count=Count("id"))
            .values_list("event_type", "count")
        )

        data = [["Tipo de Evento", "Cantidad"]]
        type_names = dict(AuditEvent.EventType.choices)
        for etype, count in sorted(by_type.items(), key=lambda x: -x[1]):
            data.append([type_names.get(etype, etype), str(count)])
        data.append(["TOTAL", str(total)])

        col_widths = [90 * mm, 30 * mm]
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a4d2e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#f5f5f5")]),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e8f5e9")),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ]))
        elements.append(table)
        return elements

    def _build_conclusions(self):
        elements = []
        elements.append(Paragraph("6. Conclusiones y Recomendaciones", self.styles["SectionHeader"]))

        findings = AuditFinding.objects.filter(status="OPEN")

        level_names = [
            "Protección contra ataques de fuerza bruta",
            "Precisión del backend para rechazar registros inválidos",
            "Resiliencia ante interrupciones en servicios AWS",
            "Aislamiento e impacto operativo al realizar cambios",
        ]
        metrics = QualityMetric.objects.filter(metric_name__in=level_names)
        level_sum = sum(int(m.value) for m in metrics)
        level_count = metrics.count()
        global_score = round((level_sum / (level_count * 5)) * 100, 1) if level_count else 0

        elements.append(Paragraph("<b>6.1. Conclusiones</b>", self.styles["Heading3"]))
        elements.append(Spacer(1, 3 * mm))

        conclusions = [
            f"El sistema SACARF obtuvo un nivel de madurez global de "
            f"<b>{global_score:.1f}%</b> (promedio de {level_count} características evaluadas con escala 1-5).",
        ]
        for m in metrics:
            level = int(m.value)
            conclusions.append(
                f"<b>{m.characteristic.code}</b> ({m.metric_name}): "
                f"Nivel {level}/5 — {m.level_descriptions[level - 1] if m.level_descriptions else ''}"
            )
        if findings.filter(finding_type="NC").exists():
            conclusions.append(
                f"Se identificaron <b>{findings.filter(finding_type='NC').count()}</b> "
                f"no conformidades que requieren acción correctiva."
            )
        if findings.filter(finding_type="OBS").exists():
            conclusions.append(
                f"Se registraron <b>{findings.filter(finding_type='OBS').count()}</b> "
                f"observaciones para mejora continua."
            )
        if findings.filter(finding_type="STR").exists():
            conclusions.append(
                f"Se identificaron <b>{findings.filter(finding_type='STR').count()}</b> "
                f"fortalezas en el sistema."
            )

        for c in conclusions:
            elements.append(Paragraph(f"• {c}", self.styles["FindingItem"]))

        elements.append(Spacer(1, 5 * mm))
        elements.append(Paragraph("<b>6.2. Recomendaciones</b>", self.styles["Heading3"]))
        elements.append(Spacer(1, 3 * mm))

        recommendations = [
            "Implementar un sistema de logging centralizado que registre todas las "
            "acciones críticas del sistema con trazabilidad completa de usuario.",
            "Establecer monitoreo continuo de la disponibilidad del servicio "
            "con alertas automáticas ante caídas del sistema.",
            "Realizar pruebas periódicas de rendimiento en el endpoint de captura "
            "facial para garantizar tiempos de respuesta aceptables.",
            "Mantener la documentación de la API actualizada y accesible.",
            "Implementar un programa de mejora continua basado en los hallazgos "
            "de esta auditoría.",
        ]

        for r in recommendations:
            elements.append(Paragraph(f"• {r}", self.styles["FindingItem"]))

        elements.append(Spacer(1, 10 * mm))
        elements.append(Paragraph(
            f"<i>Informe generado automáticamente por SACAUDIT el "
            f"{self.report.generated_at.strftime('%d/%m/%Y %H:%M')}.</i>",
            ParagraphStyle("Disclaimer", parent=self.styles["Normal"],
                           fontSize=8, textColor=colors.HexColor("#888888"),
                           alignment=TA_CENTER),
        ))

        return elements
