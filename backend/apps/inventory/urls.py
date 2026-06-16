from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, StockMovementViewSet

router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")
router.register("movements", StockMovementViewSet, basename="stockmovement")

urlpatterns = [path("", include(router.urls))]
