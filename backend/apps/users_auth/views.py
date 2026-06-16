from django.contrib.auth.models import Group, Permission
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User
from .serializers import (
    UserSerializer, MeSerializer, LoginSerializer,
    RoleSerializer, PermissionSerializer, ChangePasswordSerializer,
)


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(MeSerializer(request.user).data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        s = ChangePasswordSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        if not request.user.check_password(s.validated_data["old_password"]):
            return Response({"detail": "Old password is incorrect."}, status=400)
        request.user.set_password(s.validated_data["new_password"])
        request.user.save()
        return Response({"detail": "Password updated."})


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("username")
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    search_fields = ["username", "email", "first_name", "last_name"]


class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Group.objects.all().order_by("name")
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["get"])
    def permissions(self, request, pk=None):
        group = self.get_object()
        return Response(PermissionSerializer(group.permissions.all(), many=True).data)


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Permission.objects.select_related("content_type").order_by("codename")
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]
