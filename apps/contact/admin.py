from django.contrib import admin
from django.utils.html import format_html

from .models import ContactInquiry


@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display = (
        "created_at", "full_name", "company", "interest",
        "notification_state", "is_handled", "handled_by",
    )
    list_filter = ("is_handled", "interest", "organization_size", "created_at")
    # `message` is deliberately excluded: searching it runs an unindexed LIKE
    # over unbounded free text that routinely contains third-party incident
    # detail. Open the record to read it.
    search_fields = ("full_name", "work_email", "company", "job_title")
    # Submitted content is a record of what the sender actually wrote and
    # should not be silently rewritten; only our own workflow fields are editable.
    readonly_fields = (
        "created_at", "notified_at", "user_agent", "ip_hash",
        "full_name", "work_email", "phone", "job_title",
        "company", "country", "organization_size", "interest", "message",
    )
    list_editable = ("is_handled",)
    fieldsets = (
        ("Contact", {"fields": ("full_name", "work_email", "phone", "job_title")}),
        ("Organization", {"fields": ("company", "country", "organization_size", "interest")}),
        ("Inquiry", {"fields": ("message",)}),
        ("Lifecycle", {"fields": ("is_handled", "handled_by", "internal_notes")}),
        ("Diagnostics", {
            "fields": ("created_at", "notified_at", "user_agent", "ip_hash"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description="Notified", ordering="notified_at")
    def notification_state(self, obj):
        """Make a silently-failed notification visible in the list."""
        if obj.notified_at:
            return format_html('<span style="color:#2e7d32">&#10003;</span>')
        return format_html('<span style="color:#c62828" title="No notification was sent">&#10007;</span>')

    def has_add_permission(self, request):
        # Inquiries arrive from the public form; hand-created ones would be
        # indistinguishable from genuine submissions.
        return False
