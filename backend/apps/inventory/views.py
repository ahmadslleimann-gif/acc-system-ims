from django.db.models import Sum, F
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.permissions import HasModelPermission
from .models import Product, StockMovement, ProductSupplier
from .serializers import ProductSerializer, StockMovementSerializer, ProductSupplierSerializer
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
        from apps.common.roles import can_view_cost
        if not can_view_cost(request.user):
            return Response({"detail": "Not permitted to view inventory cost/valuation."}, status=403)
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

    @action(detail=True, methods=["get"])
    def suppliers(self, request, pk=None):
        qs = self.get_object().suppliers.select_related("supplier").all()
        return Response(ProductSupplierSerializer(qs, many=True).data)

    @action(detail=True, methods=["get"], url_path="suppliers-pdf")
    def suppliers_pdf(self, request, pk=None):
        """Printable A4 list of suppliers (and their cost) for this product."""
        from apps.reports.pdf import table_pdf_response
        product = self.get_object()
        links = product.suppliers.select_related("supplier").all()
        headers = ["Supplier", "Code", "Item code", "Cost", "Last purchase", "Preferred"]
        rows = [[
            l.supplier.name, l.supplier.code, l.supplier_item_code or "-",
            str(l.cost), str(l.last_purchase_price), "★" if l.is_preferred else "",
        ] for l in links]
        return table_pdf_response(f"Suppliers — {product.code} {product.name_en}", headers, rows,
                                  f"suppliers_{product.code}.pdf")


class ProductSupplierViewSet(viewsets.ModelViewSet):
    # Contains supplier cost data -> gated to cost-viewing roles (accountant/admin).
    queryset = ProductSupplier.objects.select_related("supplier", "product").all()
    serializer_class = ProductSupplierSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]
    filterset_fields = ["product", "supplier", "is_preferred"]
    search_fields = ["supplier__name", "product__code", "supplier_item_code"]
    required_perms = {
        "GET": ["inventory.view_productsupplier"],
        "POST": ["inventory.add_productsupplier"],
        "PUT": ["inventory.change_productsupplier"],
        "PATCH": ["inventory.change_productsupplier"],
        "DELETE": ["inventory.delete_productsupplier"],
    }


class StockMovementViewSet(viewsets.ModelViewSet):
    queryset = StockMovement.objects.select_related("product").all()
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]
    filterset_fields = ["product", "direction", "reason", "status"]
    search_fields = ["doc_no", "reference"]
    required_perms = {
        "GET": ["inventory.view_stockmovement"],
        "POST": ["inventory.add_stockmovement"],
        "PUT": ["inventory.change_stockmovement"],
        "PATCH": ["inventory.change_stockmovement"],
        "DELETE": ["inventory.delete_stockmovement"],
    }

    @action(detail=True, methods=["post"])
    def post_movement(self, request, pk=None):
        mv = services.post_movement(self.get_object(), user=request.user)
        return Response(self.get_serializer(mv).data)
