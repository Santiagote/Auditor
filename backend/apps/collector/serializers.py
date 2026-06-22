from rest_framework import serializers
from .models import AuditEvent


class AuditEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEvent
        fields = [
            "id", "event_type", "source", "user_email", "user_role",
            "action", "entity_type", "entity_id", "old_value", "new_value",
            "ip_address", "timestamp", "collected_at",
        ]
        read_only_fields = ["id", "collected_at"]


class AuditEventStatsSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    last_24h = serializers.IntegerField()
    by_type = serializers.DictField(child=serializers.IntegerField())
    by_user = serializers.DictField(child=serializers.IntegerField())
