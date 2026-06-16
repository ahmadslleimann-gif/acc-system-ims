from rest_framework import serializers
from .models import Account, SystemAccount


class AccountSerializer(serializers.ModelSerializer):
    is_leaf = serializers.BooleanField(read_only=True)
    parent_code = serializers.CharField(source="parent.code", read_only=True)

    class Meta:
        model = Account
        fields = [
            "id", "code", "name_en", "name_ar", "type", "normal_balance",
            "parent", "parent_code", "is_postable", "is_system", "is_active",
            "is_leaf", "description",
        ]
        read_only_fields = ["normal_balance", "is_system"]

    def validate(self, attrs):
        instance = self.instance
        if instance and instance.is_system:
            # Prevent re-typing / re-parenting system accounts.
            for locked in ("type", "code"):
                if locked in attrs and attrs[locked] != getattr(instance, locked):
                    raise serializers.ValidationError(
                        f"Cannot change '{locked}' on a system account."
                    )
        return attrs


class AccountTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = ["id", "code", "name_en", "name_ar", "type", "is_active", "is_postable", "children"]

    def get_children(self, obj):
        return AccountTreeSerializer(obj.children.all().order_by("code"), many=True).data


class SystemAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemAccount
        fields = ["id", "key", "account"]
