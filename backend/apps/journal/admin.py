from django.contrib import admin
from .models import JournalEntry, JournalLine


class JournalLineInline(admin.TabularInline):
    model = JournalLine
    extra = 0


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ("entry_no", "entry_date", "status", "source_type", "total_debit", "total_credit")
    list_filter = ("status", "source_type")
    search_fields = ("entry_no", "memo")
    inlines = [JournalLineInline]
