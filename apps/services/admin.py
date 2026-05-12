from django.contrib import admin

from .models import Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("title", "icon_key", "display_order", "is_published", "updated_at")
    list_editable = ("display_order", "is_published")
    list_filter = ("is_published",)
    search_fields = ("title", "short_description", "description")
    prepopulated_fields = {"slug": ("title",)}
