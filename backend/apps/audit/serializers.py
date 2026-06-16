from rest_framework import serializers
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.username", read_only=True, default="system")

    class Meta:
        model = AuditLog
        fields = ["id", "user", "user_name", "action", "model", "object_id",
                  "object_repr", "changes", "ip_address", "created_at"]
