from rest_framework import serializers
from apps.common.models import ZERO
from .models import ExpenseCategory, Expense


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = ["id", "name", "name_ar", "expense_account", "is_active"]


class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Expense
        fields = ["id", "doc_no", "category", "category_name", "date", "description",
                  "amount", "tax_rate", "tax_amount", "total", "paid_from_account",
                  "status", "receipt", "approved_by", "journal_entry"]
        read_only_fields = ["doc_no", "tax_amount", "total", "status", "approved_by", "journal_entry"]

    def create(self, validated_data):
        from apps.accounting_engine.numbering import next_document_no
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
