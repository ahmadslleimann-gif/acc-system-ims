from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, StockMovementViewSet, ProductSupplierViewSet

router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")
router.register("movements", StockMovementViewSet, basename="stockmovement")
router.register("product-suppliers", ProductSupplierViewSet, basename="productsupplier")

urlpatterns = [path("", include(router.urls))]
