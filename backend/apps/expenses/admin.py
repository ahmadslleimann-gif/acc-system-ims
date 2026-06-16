from django.contrib import admin
from .models import ExpenseCategory, Expense

admin.site.register(ExpenseCategory)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("doc_no", "description", "category", "date", "status", "total")
    list_filter = ("status", "category")
