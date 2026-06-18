from django.contrib import admin

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "price", "user", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("name", "description", "user__username", "user__email")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
