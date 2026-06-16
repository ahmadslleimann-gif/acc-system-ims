from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.permissions import HasModelPermission
from .models import Customer
from .serializers import CustomerSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]
    filterset_fields = ["is_active"]
    search_fields = ["code", "name", "name_ar", "phone", "email"]
    required_perms = {
        "POST": ["customers.add_customer"],
        "PUT": ["customers.change_customer"],
        "PATCH": ["customers.change_customer"],
        "DELETE": ["customers.delete_customer"],
    }

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["get"])
    def ledger(self, request, pk=None):
        from apps.reports.ledgers import partner_ledger
        data = partner_ledger("customer", int(pk),
                              date_from=request.query_params.get("from"),
                              date_to=request.query_params.get("to"))
        return Response(data)
