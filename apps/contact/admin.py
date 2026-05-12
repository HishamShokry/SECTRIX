from django.contrib import admin

from .models import ContactInquiry


@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display = ("created_at", "full_name", "company", "interest", "is_handled", "handled_by")
    list_filter = ("is_handled", "interest", "organization_size", "created_at")
    search_fields = ("full_name", "work_email", "company", "job_title", "message")
    readonly_fields = ("created_at", "user_agent", "ip_hash")
    list_editable = ("is_handled",)
    fieldsets = (
        ("Contact", {"fields": ("full_name", "work_email", "phone", "job_title")}),
        ("Organization", {"fields": ("company", "country", "organization_size", "interest")}),
        ("Inquiry", {"fields": ("message",)}),
        ("Lifecycle", {"fields": ("is_handled", "handled_by", "internal_notes")}),
        ("Diagnostics", {"fields": ("created_at", "user_agent", "ip_hash"), "classes": ("collapse",)}),
    )
