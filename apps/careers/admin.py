from django.contrib import admin

from .models import JobOpening


@admin.register(JobOpening)
class JobOpeningAdmin(admin.ModelAdmin):
    list_display = ("title", "department", "level", "employment_type", "location", "is_remote_friendly", "is_published", "posted_at")
    list_editable = ("is_published",)
    list_filter = ("department", "level", "employment_type", "is_remote_friendly", "is_published")
    search_fields = ("title", "summary", "description")
    prepopulated_fields = {"slug": ("title",)}
