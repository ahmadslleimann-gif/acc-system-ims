from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.permissions import HasModelPermission
from .models import Supplier
from .serializers import SupplierSerializer


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]
    filterset_fields = ["is_active"]
    search_fields = ["code", "name", "name_ar", "phone", "email"]
    required_perms = {
        "POST": ["suppliers.add_supplier"],
        "PUT": ["suppliers.change_supplier"],
        "PATCH": ["suppliers.change_supplier"],
        "DELETE": ["suppliers.delete_supplier"],
    }

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["get"])
    def ledger(self, request, pk=None):
        from apps.reports.ledgers import partner_ledger
        data = partner_ledger("supplier", int(pk),
                              date_from=request.query_params.get("from"),
                              date_to=request.query_params.get("to"))
        return Response(data)
