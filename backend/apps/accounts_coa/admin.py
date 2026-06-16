from django.contrib import admin
from .models import Account, SystemAccount


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("code", "name_en", "type", "normal_balance", "is_postable", "is_system", "is_active")
    list_filter = ("type", "is_postable", "is_system", "is_active")
    search_fields = ("code", "name_en", "name_ar")


admin.site.register(SystemAccount)
