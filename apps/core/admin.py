from django.contrib import admin

from .models import (
    CompanyValue,
    CulturePillar,
    ExpertisePillar,
    HomeFeature,
    HomeStat,
    LeadershipMember,
    SiteSettings,
    TimelineEntry,
    TrustedByLogo,
)


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
