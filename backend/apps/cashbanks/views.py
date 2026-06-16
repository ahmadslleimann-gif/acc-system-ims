from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import CashBankAccount, CashTransaction
from .serializers import CashBankAccountSerializer, CashTransactionSerializer
from . import services


class CashBankAccountViewSet(viewsets.ModelViewSet):
    queryset = CashBankAccount.objects.select_related("gl_account").all()
    serializer_class = CashBankAccountSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["kind", "is_active"]
    search_fields = ["name", "bank_name", "account_number"]


class CashTransactionViewSet(viewsets.ModelViewSet):
    queryset = CashTransaction.objects.select_related("account").all()
    serializer_class = CashTransactionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["type", "status", "account"]
    search_fields = ["doc_no", "memo"]

    @action(detail=True, methods=["post"])
    def post_tx(self, request, pk=None):
        tx = services.post_transaction(self.get_object(), user=request.user)
        return Response(self.get_serializer(tx).data)
