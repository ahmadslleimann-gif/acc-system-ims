from django.db.models import Sum
from rest_framework import serializers
from .models import CashBankAccount, CashTransaction


class CashBankAccountSerializer(serializers.ModelSerializer):
    balance = serializers.SerializerMethodField()
    gl_code = serializers.CharField(source="gl_account.code", read_only=True)

    class Meta:
        model = CashBankAccount
        fields = ["id", "name", "kind", "gl_account", "gl_code", "bank_name",
                  "account_number", "iban", "is_active", "balance"]

    def get_balance(self, obj):
        from apps.journal.models import JournalLine, JournalEntry
        agg = JournalLine.objects.filter(
            account=obj.gl_account, entry__status=JournalEntry.Status.POSTED
        ).aggregate(d=Sum("debit"), c=Sum("credit"))
        return (agg["d"] or 0) - (agg["c"] or 0)


class CashTransactionSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source="account.name", read_only=True)

    class Meta:
        model = CashTransaction
        fields = ["id", "doc_no", "type", "date", "account", "account_name",
                  "contra_account", "destination_account", "amount", "status",
                  "memo", "journal_entry"]
        read_only_fields = ["doc_no", "status", "journal_entry"]

    def create(self, validated_data):
        from apps.accounting_engine.numbering import next_document_no
        return CashTransaction.objects.create(
            doc_no=next_document_no(CashTransaction, "CT"),
            created_by=self.context["request"].user, **validated_data,
        )
