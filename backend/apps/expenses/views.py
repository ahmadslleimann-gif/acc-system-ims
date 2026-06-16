from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.permissions import HasModelPermission
from .models import ExpenseCategory, Expense
from .serializers import ExpenseCategorySerializer, ExpenseSerializer
from . import services


class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    queryset = ExpenseCategory.objects.select_related("expense_account").all()
    serializer_class = ExpenseCategorySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["is_active"]
    search_fields = ["name", "name_ar"]


class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.select_related("category").all()
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]
    filterset_fields = ["category", "status", "date"]
    search_fields = ["doc_no", "description"]
    required_perms = {
        "POST": ["expenses.add_expense"],
        "PUT": ["expenses.change_expense"],
        "PATCH": ["expenses.change_expense"],
        "DELETE": ["expenses.delete_expense"],
    }

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        exp = self.get_object()
        if exp.status != Expense.Status.DRAFT:
            return Response({"detail": "Only DRAFT can be submitted."}, status=400)
        exp.status = Expense.Status.PENDING
        exp.save(update_fields=["status"])
        return Response(self.get_serializer(exp).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        exp = self.get_object()
        if exp.status != Expense.Status.PENDING:
            return Response({"detail": "Only PENDING can be approved."}, status=400)
        exp.status = Expense.Status.APPROVED
        exp.approved_by = request.user
        exp.save(update_fields=["status", "approved_by"])
        return Response(self.get_serializer(exp).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        exp = self.get_object()
        exp.status = Expense.Status.REJECTED
        exp.save(update_fields=["status"])
        return Response(self.get_serializer(exp).data)

    @action(detail=True, methods=["post"])
    def post_expense(self, request, pk=None):
        exp = services.post_expense(self.get_object(), user=request.user)
        return Response(self.get_serializer(exp).data)
