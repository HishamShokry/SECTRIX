from django.contrib import admin
from django.utils.functional import lazy

from .models import (
    CompanyValue,
    CulturePillar,
    ExpertisePillar,
    HomeFeature,
    HomeStat,
    LeadershipMember,
    SiteSettings,
    SocialLink,
    TimelineEntry,
    TrustedByLogo,
)


def _site_name() -> str:
    """Admin branding follows the editable site name.

    Falls back to a literal if the table is not migrated yet, so the admin
    stays reachable on a fresh database.
    """
    try:
        return SiteSettings.load().name
    except Exception:
        return "Sectrex Consulting"


def _admin_title() -> str:
    return f"{_site_name()} Admin"


admin.site.site_header = lazy(_site_name, str)()
admin.site.site_title = lazy(_admin_title, str)()
admin.site.index_title = "Operations Console"


class ContentAdmin(admin.ModelAdmin):
    """Shared defaults: ordering controls visible and editable from the list."""

    list_editable = ("display_order", "is_published")
    list_filter = ("is_published",)
    ordering = ("display_order", "pk")


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Identity", {"fields": ("name", "tagline", "description", "keywords")}),
        ("Contact", {"fields": ("email", "phone", "address")}),
        ("Links", {"fields": ("url", "twitter")}),
    )

    def has_add_permission(self, request):
        # Singleton: only ever one row, created on first load().
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SocialLink)
class SocialLinkAdmin(ContentAdmin):
    list_display = ("name", "icon_key", "url", "display_order", "is_published")
    list_filter = ("is_published", "icon_key")


@admin.register(TrustedByLogo)
class TrustedByLogoAdmin(ContentAdmin):
    list_display = ("name", "display_order", "is_published")


@admin.register(HomeStat)
class HomeStatAdmin(ContentAdmin):
    list_display = ("value", "suffix", "label", "display_order", "is_published")


@admin.register(HomeFeature)
class HomeFeatureAdmin(ContentAdmin):
    list_display = ("title", "icon_key", "display_order", "is_published")
    list_filter = ("is_published", "icon_key")


@admin.register(CompanyValue)
class CompanyValueAdmin(ContentAdmin):
    list_display = ("title", "display_order", "is_published")


@admin.register(ExpertisePillar)
class ExpertisePillarAdmin(ContentAdmin):
    list_display = ("tag", "title", "display_order", "is_published")


@admin.register(LeadershipMember)
class LeadershipMemberAdmin(ContentAdmin):
    list_display = ("name", "role", "initials", "display_order", "is_published")


@admin.register(TimelineEntry)
class TimelineEntryAdmin(ContentAdmin):
    list_display = ("year", "title", "display_order", "is_published")


@admin.register(CulturePillar)
class CulturePillarAdmin(ContentAdmin):
    list_display = ("tag", "title", "display_order", "is_published")
