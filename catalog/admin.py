from django.contrib import admin

from common.admin import SoftDeleteAdmin

from .models import (
    Category,
    Product,
    ProductImage,
    Review,
    Sale,
    Specification,
    Tag,
)


@admin.register(Category)
class CategoryAdmin(SoftDeleteAdmin):
    list_display = (
        "title",
        "parent",
        "is_active",
        "is_favorite",
        "sort_index",
        "is_deleted",
    )
    list_filter = ("is_active", "is_favorite", "is_deleted")
    search_fields = ("title",)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class SpecificationInline(admin.TabularInline):
    model = Specification
    extra = 1


@admin.register(Product)
class ProductAdmin(SoftDeleteAdmin):
    list_display = (
        "title",
        "category",
        "price",
        "count",
        "limited_edition",
        "is_banner",
        "sort_index",
        "purchases_count",
        "is_deleted",
    )
    list_filter = (
        "category",
        "free_delivery",
        "limited_edition",
        "is_banner",
        "is_deleted",
    )
    search_fields = ("title", "description")
    filter_horizontal = ("tags",)
    inlines = [ProductImageInline, SpecificationInline]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "author", "rate", "date")
    list_filter = ("rate",)
    search_fields = ("author", "email", "text")


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("product", "sale_price", "date_from", "date_to")
    list_filter = ("date_from", "date_to")
