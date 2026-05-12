from django.contrib import admin

from .models import CaseStudy


@admin.register(CaseStudy)
class CaseStudyAdmin(admin.ModelAdmin):
    list_display = ("client_name", "title", "sector", "region", "is_published", "published_at", "display_order")
    list_editable = ("is_published", "display_order")
    list_filter = ("sector", "region", "is_published")
    search_fields = ("client_name", "title", "summary", "challenge", "approach", "outcome")
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        (None, {"fields": ("title", "slug", "client_name", "sector", "region", "summary")}),
        ("Narrative", {"fields": ("challenge", "approach", "outcome")}),
        ("Headline metric", {"fields": ("headline_metric", "headline_metric_label")}),
        ("Media & taxonomy", {"fields": ("cover_image", "tags")}),
        ("Publishing", {"fields": ("is_published", "published_at", "display_order")}),
    )
