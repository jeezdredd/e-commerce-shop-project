from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "number", "status", "error_text", "created_at")
    list_filter = ("status",)
    search_fields = ("number", "order__id")
