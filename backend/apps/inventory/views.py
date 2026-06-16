from django.db.models import Sum, F
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.permissions import HasModelPermission
from .models import Product, StockMovement
from .serializers import ProductSerializer, StockMovementSerializer
from . import services


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]
    filterset_fields = ["kind", "is_active"]
    search_fields = ["code", "name_en", "name_ar", "barcode"]
    required_perms = {
        "POST": ["inventory.add_product"],
        "PUT": ["inventory.change_product"],
        "PATCH": ["inventory.change_product"],
        "DELETE": ["inventory.delete_product"],
    }

    @action(detail=False, methods=["get"])
    def low_stock(self, request):
        items = [p for p in self.get_queryset().filter(kind=Product.Kind.STOCK, is_active=True) if p.is_low_stock]
        return Response(ProductSerializer(items, many=True).data)

    @action(detail=False, methods=["get"])
    def valuation(self, request):
        products = self.get_queryset().filter(kind=Product.Kind.STOCK)
        rows = [
            {"code": p.code, "name": p.name_en, "qty": str(p.quantity_on_hand),
             "avg_cost": str(p.average_cost), "value": str(p.stock_value)}
            for p in products
        ]
        total = sum(p.stock_value for p in products)
        return Response({"rows": rows, "total_value": str(total)})

    @action(detail=True, methods=["get"])
    def movements(self, request, pk=None):
        qs = self.get_object().movements.all()
        return Response(StockMovementSerializer(qs, many=True).data)


class StockMovementViewSet(viewsets.ModelViewSet):
    queryset = StockMovement.objects.select_related("product").all()
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["product", "direction", "reason", "status"]
    search_fields = ["doc_no", "reference"]

    @action(detail=True, methods=["post"])
    def post_movement(self, request, pk=None):
        mv = services.post_movement(self.get_object(), user=request.user)
        return Response(self.get_serializer(mv).data)
