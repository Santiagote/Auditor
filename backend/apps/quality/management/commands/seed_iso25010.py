from django.core.management.base import BaseCommand
from apps.quality.models import IsoCharacteristic, IsoSubcharacteristic


class Command(BaseCommand):
    help = "Siembra las características y subcaracterísticas ISO 25010"

    def handle(self, *args, **options):
        data = {
            "FUN": {
                "name": "Functional Suitability",
                "description": "Grado en que un producto o sistema proporciona funciones que satisfacen las necesidades declaradas e implícitas cuando se usa en condiciones especificadas.",
                "weight": 1.0,
                "subs": [
                    ("Functional Completeness", "Grado en que el conjunto de funciones cubre todas las tareas y objetivos del usuario especificados."),
                    ("Functional Correctness", "Grado en que un producto o sistema proporciona los resultados correctos con el grado de precisión necesario."),
                    ("Functional Appropriateness", "Grado en que las funciones facilitan la realización de tareas y objetivos especificados."),
                ],
            },
            "REL": {
                "name": "Reliability",
                "description": "Grado en que un sistema, producto o componente realiza funciones especificadas durante un período de tiempo determinado en condiciones especificadas.",
                "weight": 1.0,
                "subs": [
                    ("Maturity", "Grado en que un sistema satisface las necesidades de fiabilidad en condiciones normales de funcionamiento."),
                    ("Availability", "Grado en que un sistema está operativo y accesible cuando se requiere su uso."),
                    ("Fault Tolerance", "Grado en que un sistema opera según lo previsto a pesar de la presencia de fallos hardware o software."),
                    ("Recoverability", "Grado en que un producto o sistema puede recuperar los datos directamente afectados y restablecer el estado deseado del sistema en caso de interrupción o fallo."),
                ],
            },
            "PER": {
                "name": "Performance Efficiency",
                "description": "Rendimiento relativo a la cantidad de recursos utilizados bajo condiciones determinadas.",
                "weight": 1.0,
                "subs": [
                    ("Time Behavior", "Grado en que los tiempos de respuesta, tiempos de procesamiento y tasas de rendimiento de un producto o sistema cumplen los requisitos."),
                    ("Resource Utilization", "Grado en que las cantidades y tipos de recursos utilizados por un producto o sistema cumplen los requisitos."),
                    ("Capacity", "Grado en que los límites máximos de un parámetro de un producto o sistema cumplen los requisitos."),
                ],
            },
            "SEC": {
                "name": "Security",
                "description": "Grado en que un producto o sistema protege la información y los datos de manera que las personas u otros productos o sistemas tengan el grado de acceso a los datos adecuado a sus tipos y niveles de autorización.",
                "weight": 1.5,
                "subs": [
                    ("Confidentiality", "Grado en que un producto o sistema garantiza que los datos solo sean accesibles para quienes estén autorizados a tener acceso."),
                    ("Integrity", "Grado en que un sistema, producto o componente evita el acceso no autorizado o la modificación de programas o datos informáticos."),
                    ("Non-repudiation", "Grado en que se pueden demostrar las acciones o eventos ocurridos para que no se puedan negar posteriormente."),
                    ("Accountability", "Grado en que las acciones de una entidad pueden rastrearse de forma exclusiva hasta dicha entidad."),
                    ("Authenticity", "Grado en que se puede demostrar que la identidad de un sujeto o recurso es la que se declara."),
                ],
            },
            "COM": {
                "name": "Compatibility",
                "description": "Grado en que un producto, sistema o componente puede intercambiar información con otros productos, sistemas o componentes, y/o realizar las funciones requeridas mientras comparte el mismo entorno hardware o software.",
                "weight": 0.8,
                "subs": [
                    ("Co-existence", "Grado en que un producto puede realizar sus funciones requeridas de manera eficiente mientras comparte un entorno y recursos comunes con otros productos, sin que se afecte negativamente."),
                    ("Interoperability", "Grado en que dos o más sistemas, productos o componentes pueden intercambiar información y utilizar la información intercambiada."),
                ],
            },
            "USA": {
                "name": "Usability",
                "description": "Grado en que un producto o sistema puede ser utilizado por usuarios específicos para lograr objetivos específicos con efectividad, eficiencia y satisfacción en un contexto de uso específico.",
                "weight": 0.8,
                "subs": [
                    ("Appropriateness Recognizability", "Grado en que los usuarios pueden reconocer si un producto o sistema es adecuado para sus necesidades."),
                    ("Learnability", "Grado en que un producto o sistema puede ser aprendido por los usuarios específicos."),
                    ("Operability", "Grado en que un producto o sistema es fácil de operar y controlar."),
                    ("User Error Protection", "Grado en que un sistema protege a los usuarios de cometer errores."),
                    ("Accessibility", "Grado en que un producto o sistema puede ser utilizado por personas con el más amplio rango de características y capacidades."),
                ],
            },
            "MAI": {
                "name": "Maintainability",
                "description": "Grado de efectividad y eficiencia con que un producto o sistema puede ser modificado para mejorarlo, corregirlo o adaptarlo a cambios en el entorno y en los requisitos.",
                "weight": 0.8,
                "subs": [
                    ("Modularity", "Grado en que un sistema está compuesto de componentes discretos."),
                    ("Reusability", "Grado en que un activo puede ser utilizado en más de un sistema."),
                    ("Analyzability", "Grado en que se puede evaluar el impacto de un cambio en un producto o sistema."),
                    ("Modifiability", "Grado en que un producto o sistema puede ser modificado de manera efectiva y eficiente."),
                    ("Testability", "Grado en que se pueden establecer criterios de prueba para un sistema y realizar las pruebas."),
                ],
            },
            "POR": {
                "name": "Portability",
                "description": "Grado de efectividad y eficiencia con que un sistema, producto o componente puede transferirse de un entorno hardware, software o de otro tipo a otro.",
                "weight": 0.6,
                "subs": [
                    ("Adaptability", "Grado en que un producto o sistema puede adaptarse de forma efectiva y eficiente a entornos hardware, software u operacionales diferentes."),
                    ("Installability", "Grado en que un producto o sistema puede instalarse y/o desinstalarse de forma efectiva y eficiente."),
                    ("Replaceability", "Grado en que un producto puede reemplazar a otro producto de software del mismo propósito."),
                ],
            },
        }

        for code, info in data.items():
            char, created = IsoCharacteristic.objects.get_or_create(
                code=code,
                defaults={
                    "name": info["name"],
                    "description": info["description"],
                    "weight": info["weight"],
                },
            )
            if created:
                self.stdout.write(f"Creada característica: [{code}] {info['name']}")
            else:
                self.stdout.write(f"Ya existe: [{code}] {info['name']}")

            for sub_name, sub_desc in info["subs"]:
                sub, sub_created = IsoSubcharacteristic.objects.get_or_create(
                    characteristic=char,
                    name=sub_name,
                    defaults={"description": sub_desc},
                )
                if sub_created:
                    self.stdout.write(f"  + Sub: {sub_name}")

        self.stdout.write(self.style.SUCCESS("Seed ISO 25010 completado exitosamente"))
