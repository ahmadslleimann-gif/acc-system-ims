from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AccountViewSet, SystemAccountViewSet

router = DefaultRouter()
router.register("accounts", AccountViewSet, basename="account")
router.register("system-accounts", SystemAccountViewSet, basename="systemaccount")

urlpatterns = [path("", include(router.urls))]
