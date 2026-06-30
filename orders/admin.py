from django.contrib import admin

from common.admin import SoftDeleteAdmin

from .models import DeliverySettings, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(SoftDeleteAdmin):
    list_display = (
        "id",
        "user",
        "created_at",
        "delivery_type",
        "payment_type",
        "total_cost",
        "status",
        "is_deleted",
    )
    list_filter = ("status", "delivery_type", "payment_type", "is_deleted")
    search_fields = ("full_name", "email", "phone")
    inlines = [OrderItemInline]


@admin.register(DeliverySettings)
class DeliverySettingsAdmin(admin.ModelAdmin):
    list_display = ("express_price", "free_threshold", "base_delivery_price")

    def has_add_permission(self, request):
        return not DeliverySettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
