from django.db.models import Sum
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.permissions import HasModelPermission
from apps.journal.models import JournalLine, JournalEntry
from .models import Account, SystemAccount
from .serializers import AccountSerializer, AccountTreeSerializer, SystemAccountSerializer


class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]
    filterset_fields = ["type", "is_active", "is_postable", "parent"]
    search_fields = ["code", "name_en", "name_ar"]
    required_perms = {
        "POST": ["accounts_coa.add_account"],
        "PUT": ["accounts_coa.change_account"],
        "PATCH": ["accounts_coa.change_account"],
        "DELETE": ["accounts_coa.delete_account"],
    }

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        account = self.get_object()
        if account.is_system:
            return Response({"detail": "System accounts cannot be deleted."}, status=400)
        if account.children.exists():
            return Response({"detail": "Delete child accounts first."}, status=400)
        if JournalLine.objects.filter(account=account).exists():
            return Response({"detail": "Account has journal lines; deactivate instead."}, status=400)
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=["get"])
    def tree(self, request):
        roots = Account.objects.filter(parent__isnull=True).order_by("code")
        return Response(AccountTreeSerializer(roots, many=True).data)

    @action(detail=True, methods=["get"])
    def balance(self, request, pk=None):
        """Net balance of a single account from posted journal lines."""
        account = self.get_object()
        agg = JournalLine.objects.filter(
            account=account, entry__status=JournalEntry.Status.POSTED
        ).aggregate(d=Sum("debit"), c=Sum("credit"))
        debit = agg["d"] or 0
        credit = agg["c"] or 0
        net = (debit - credit) if account.normal_balance == "DEBIT" else (credit - debit)
        return Response({"account": account.code, "debit": debit, "credit": credit, "balance": net})


class SystemAccountViewSet(viewsets.ModelViewSet):
    queryset = SystemAccount.objects.select_related("account")
    serializer_class = SystemAccountSerializer
    permission_classes = [IsAuthenticated]
