from rest_framework import serializers
from .models import IsoCharacteristic, IsoSubcharacteristic, QualityMetric, AuditFinding


class IsoSubcharacteristicSerializer(serializers.ModelSerializer):
    class Meta:
        model = IsoSubcharacteristic
        fields = ["id", "name", "description"]


class IsoCharacteristicSerializer(serializers.ModelSerializer):
    subcharacteristics = IsoSubcharacteristicSerializer(many=True, read_only=True)

    class Meta:
        model = IsoCharacteristic
        fields = ["id", "code", "name", "description", "weight", "subcharacteristics"]


class QualityMetricSerializer(serializers.ModelSerializer):
    characteristic_code = serializers.CharField(source="characteristic.code", read_only=True)
    characteristic_name = serializers.CharField(source="characteristic.name", read_only=True)
    subcharacteristic_name = serializers.CharField(source="subcharacteristic.name", read_only=True, default="")
    level_label = serializers.SerializerMethodField()

    class Meta:
        model = QualityMetric
        fields = [
            "id", "characteristic", "characteristic_code", "characteristic_name",
            "subcharacteristic", "subcharacteristic_name",
            "metric_name", "value", "target", "unit", "status", "formula",
            "level_descriptions", "level_label", "measured_at",
        ]

    def get_level_label(self, obj):
        return f"Nivel {int(obj.value)}/5"


class AuditFindingSerializer(serializers.ModelSerializer):
    characteristic_code = serializers.CharField(source="characteristic.code", read_only=True, default="")
    characteristic_name = serializers.CharField(source="characteristic.name", read_only=True, default="")

    class Meta:
        model = AuditFinding
        fields = [
            "id", "finding_type", "characteristic", "characteristic_code", "characteristic_name",
            "severity", "description", "evidence", "status", "corrective_action",
            "created_at", "resolved_at",
        ]
        read_only_fields = ["id", "created_at"]
