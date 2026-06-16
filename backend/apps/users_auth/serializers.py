from django.contrib.auth.models import Group, Permission
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["id", "name"]


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "codename", "name"]


class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    role_ids = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(), many=True, write_only=True, source="groups", required=False
    )
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name", "phone",
            "preferred_language", "is_active", "is_superuser",
            "roles", "role_ids", "password",
        ]
        read_only_fields = ["is_superuser"]

    def get_roles(self, obj):
        return obj.role_names()

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        groups = validated_data.pop("groups", [])
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        user.groups.set(groups)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        groups = validated_data.pop("groups", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        if groups is not None:
            instance.groups.set(groups)
        return instance


class MeSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "preferred_language", "is_superuser", "roles", "permissions",
        ]

    def get_roles(self, obj):
        return obj.role_names()

    def get_permissions(self, obj):
        if obj.is_superuser:
            return ["*"]
        return sorted(obj.get_all_permissions())


class LoginSerializer(TokenObtainPairSerializer):
    """Adds user profile + roles to the JWT login response."""

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = MeSerializer(self.user).data
        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
