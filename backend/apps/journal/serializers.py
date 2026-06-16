from decimal import Decimal
from rest_framework import serializers

from apps.common.models import ZERO
from .models import JournalEntry, JournalLine


class JournalLineSerializer(serializers.ModelSerializer):
    account_code = serializers.CharField(source="account.code", read_only=True)
    account_name = serializers.CharField(source="account.name_en", read_only=True)

    class Meta:
        model = JournalLine
        fields = [
            "id", "account", "account_code", "account_name",
            "debit", "credit", "line_memo", "is_cleared",
        ]


class JournalEntrySerializer(serializers.ModelSerializer):
    lines = JournalLineSerializer(many=True)
    total_debit = serializers.DecimalField(max_digits=19, decimal_places=4, read_only=True)
    total_credit = serializers.DecimalField(max_digits=19, decimal_places=4, read_only=True)
    is_balanced = serializers.BooleanField(read_only=True)

    class Meta:
        model = JournalEntry
        fields = [
            "id", "entry_no", "entry_date", "status", "memo",
            "source_type", "source_id", "reversed_entry",
            "total_debit", "total_credit", "is_balanced",
            "lines", "posted_at", "created_at",
        ]
        read_only_fields = ["entry_no", "status", "posted_at", "source_type", "source_id"]

    def validate(self, attrs):
        lines = attrs.get("lines", [])
        if len(lines) < 2:
            raise serializers.ValidationError("An entry needs at least two lines.")
        total_debit = sum((l.get("debit") or ZERO for l in lines), ZERO)
        total_credit = sum((l.get("credit") or ZERO for l in lines), ZERO)
        if total_debit != total_credit:
            raise serializers.ValidationError(
                f"Entry is unbalanced: debit {total_debit} != credit {total_credit}."
            )
        if total_debit == 0:
            raise serializers.ValidationError("Entry total cannot be zero.")
        return attrs

    def create(self, validated_data):
        from apps.accounting_engine.numbering import next_entry_no
        lines = validated_data.pop("lines")
        entry = JournalEntry.objects.create(
            entry_no=next_entry_no(validated_data["entry_date"]),
            status=JournalEntry.Status.DRAFT,
            created_by=self.context["request"].user,
            **validated_data,
        )
        JournalLine.objects.bulk_create([JournalLine(entry=entry, **l) for l in lines])
        return entry

    def update(self, instance, validated_data):
        if instance.status != JournalEntry.Status.DRAFT:
            raise serializers.ValidationError("Only DRAFT entries can be edited.")
        lines = validated_data.pop("lines", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if lines is not None:
            instance.lines.all().delete()
            JournalLine.objects.bulk_create([JournalLine(entry=instance, **l) for l in lines])
        return instance
