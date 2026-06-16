from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "action", "model", "object_id", "object_repr")
    list_filter = ("action", "model")
    search_fields = ("object_repr", "object_id")
    readonly_fields = [f.name for f in AuditLog._meta.fields]
