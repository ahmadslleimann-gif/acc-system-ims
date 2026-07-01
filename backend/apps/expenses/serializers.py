from rest_framework import serializers
from apps.common.models import ZERO
from .models import ExpenseCategory, Expense


def _default_expense_account():
    """A sensible general expense account (first postable EXPENSE account)."""
    from apps.accounts_coa.models import Account
    return Account.objects.filter(type="EXPENSE", is_postable=True, is_active=True).order_by("code").first()


class ExpenseCategorySerializer(serializers.ModelSerializer):
    expense_account = serializers.PrimaryKeyRelatedField(
        queryset=__import__("apps.accounts_coa.models", fromlist=["Account"]).Account.objects.all(),
        required=False, allow_null=True,
    )

    class Meta:
        model = ExpenseCategory
        fields = ["id", "name", "name_ar", "expense_account", "is_active"]

    def create(self, validated_data):
        # Default the GL account so non-accountants can create categories simply.
        if not validated_data.get("expense_account"):
            validated_data["expense_account"] = _default_expense_account()
        return super().create(validated_data)


class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    paid_from_account = serializers.PrimaryKeyRelatedField(
        queryset=__import__("apps.accounts_coa.models", fromlist=["Account"]).Account.objects.all(),
        required=False, allow_null=True,
    )

    class Meta:
        model = Expense
        fields = ["id", "doc_no", "category", "category_name", "date", "description",
                  "amount", "tax_rate", "tax_amount", "total", "paid_from_account",
                  "status", "receipt", "approved_by", "journal_entry"]
        read_only_fields = ["doc_no", "tax_amount", "total", "status", "approved_by", "journal_entry"]

    def create(self, validated_data):
        from apps.accounting_engine.numbering import next_document_no
        from apps.accounts_coa.models import SystemAccount
        if not validated_data.get("paid_from_account"):
            validated_data["paid_from_account"] = SystemAccount.objects.get(key="CASH").account
        amount = validated_data.get("amount", ZERO)
        rate = validated_data["tax_rate"].fraction() if validated_data.get("tax_rate") else ZERO
        tax = (amount * rate).quantize(ZERO)
        validated_data["tax_amount"] = tax
        validated_data["total"] = amount + tax
        return Expense.objects.create(
            doc_no=next_document_no(Expense, "EXP"),
            created_by=self.context["request"].user, **validated_data,
        )

    def update(self, instance, validated_data):
        if instance.status in (Expense.Status.POSTED,):
            raise serializers.ValidationError("Posted expenses cannot be edited.")
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        rate = instance.tax_rate.fraction() if instance.tax_rate else ZERO
        instance.tax_amount = (instance.amount * rate).quantize(ZERO)
        instance.total = instance.amount + instance.tax_amount
        instance.save()
        return instance
