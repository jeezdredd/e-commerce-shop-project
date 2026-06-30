from django.contrib import admin


class SoftDeleteAdmin(admin.ModelAdmin):
    actions = ["soft_delete_selected", "restore_selected"]

    def get_queryset(self, request):
        return self.model.all_objects.all()

    def delete_model(self, request, obj):
        obj.delete()

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete()

    @admin.action(description="Мягко удалить выбранные")
    def soft_delete_selected(self, request, queryset):
        for obj in queryset:
            obj.delete()

    @admin.action(description="Восстановить выбранные")
    def restore_selected(self, request, queryset):
        for obj in queryset:
            obj.restore()
