"""Editable site content.

Everything the public pages render — copy, stats, leadership, timeline — lives
here so it can be maintained from the admin rather than in code.

Field names deliberately match the template variables they replaced, so the
templates did not have to change when this content moved out of
``apps.core.content``.
"""
from django.core.cache import cache
from django.db import models

from apps.core.icons import ICON_CHOICES, render_icon


class PublishedOrderedQuerySet(models.QuerySet):
    def live(self):
        return self.filter(is_published=True)


class ContentBase(models.Model):
    """Shared publishing controls for every editable content block."""

    display_order = models.PositiveIntegerField(
        default=0, help_text="Lower numbers appear first."
    )
    is_published = models.BooleanField(
        default=True, help_text="Untick to hide from the site without deleting."
    )

    objects = PublishedOrderedQuerySet.as_manager()

    class Meta:
        abstract = True
        ordering = ["display_order", "pk"]


class IconMixin(models.Model):
    icon_key = models.CharField(
        max_length=40,
        choices=ICON_CHOICES,
        default="shield",
        help_text="Pick from the built-in icon set.",
    )

    class Meta:
        abstract = True

    @property
    def icon(self) -> str:
        """Inline SVG, so templates can keep using ``{{ obj.icon|safe }}``."""
        return render_icon(self.icon_key)


class SiteSettings(models.Model):
    """Site-wide identity and contact details. A single row.

    Replaces the hardcoded ``settings.SITE_META`` dict. Field names match the
    keys that dict used, so ``{{ site.name }}`` and friends still resolve.
    """

    CACHE_KEY = "core.sitesettings"

    name = models.CharField(max_length=120, default="Sectrex Consulting")
    tagline = models.CharField(max_length=200, blank=True)
    description = models.TextField(
        help_text="Default meta description, used when a page does not set one."
    )
    keywords = models.CharField(max_length=400, blank=True)
    url = models.URLField(
        default="https://sectrexconsulting.com",
        help_text="Canonical public URL, used to build absolute links.",
    )
    twitter = models.CharField(max_length=40, blank=True, help_text='Including the "@".')
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    address = models.CharField(max_length=240, blank=True)

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        # Singleton: always row 1, so the admin can never create a second.
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete(self.CACHE_KEY)

    def delete(self, *args, **kwargs):  # pragma: no cover - guarded in admin too
        """Refuse deletion; the site needs these values to render."""
        return

    @classmethod
    def load(cls) -> "SiteSettings":
        """Return the singleton, creating it from defaults if absent.

        Cached because every request renders it through the context processor.
        """
        obj = cache.get(cls.CACHE_KEY)
        if obj is None:
            obj, _ = cls.objects.get_or_create(pk=1)
            cache.set(cls.CACHE_KEY, obj, 300)
        return obj


class TrustedByLogo(ContentBase):
    """Client names in the home-page trust strip."""

    name = models.CharField(max_length=120)

    class Meta(ContentBase.Meta):
        verbose_name = "Trusted-By Entry"
        verbose_name_plural = "Trusted-By Entries"

    def __str__(self) -> str:
        # Templates iterate this list and render the object directly.
        return self.name


class HomeStat(ContentBase):
    value = models.CharField(max_length=20, help_text='The number, e.g. "99.97".')
    suffix = models.CharField(
        max_length=10, blank=True, help_text='Accent-coloured suffix, e.g. "%" or "+".'
    )
    label = models.CharField(max_length=120)

    class Meta(ContentBase.Meta):
        verbose_name = "Home Stat"
        verbose_name_plural = "Home Stats"

    def __str__(self) -> str:
        return f"{self.value}{self.suffix} — {self.label}"


class HomeFeature(ContentBase, IconMixin):
    title = models.CharField(max_length=140)
    body = models.TextField()

    class Meta(ContentBase.Meta):
        verbose_name = "Home Feature"
        verbose_name_plural = "Home Features"

    def __str__(self) -> str:
        return self.title


class CompanyValue(ContentBase):
    title = models.CharField(max_length=140)
    body = models.TextField()

    class Meta(ContentBase.Meta):
        verbose_name = "Company Value"
        verbose_name_plural = "Company Values"

    def __str__(self) -> str:
        return self.title


class ExpertisePillar(ContentBase):
    tag = models.CharField(max_length=60, help_text="Small mono label above the title.")
    title = models.CharField(max_length=140)
    body = models.TextField()

    class Meta(ContentBase.Meta):
        verbose_name = "Expertise Pillar"
        verbose_name_plural = "Expertise Pillars"

    def __str__(self) -> str:
        return self.title


class LeadershipMember(ContentBase):
    name = models.CharField(max_length=120)
    role = models.CharField(max_length=140)
    bio = models.TextField()
    initials = models.CharField(
        max_length=4, help_text="Shown in the avatar circle, e.g. \"HA\"."
    )

    class Meta(ContentBase.Meta):
        verbose_name = "Leadership Member"
        verbose_name_plural = "Leadership"

    def __str__(self) -> str:
        return f"{self.name} — {self.role}"


class TimelineEntry(ContentBase):
    year = models.CharField(max_length=10)
    title = models.CharField(max_length=140)
    body = models.TextField()

    class Meta(ContentBase.Meta):
        verbose_name = "Timeline Entry"
        verbose_name_plural = "Timeline"

    def __str__(self) -> str:
        return f"{self.year} — {self.title}"


class CulturePillar(ContentBase):
    tag = models.CharField(max_length=60)
    title = models.CharField(max_length=140)
    body = models.TextField()

    class Meta(ContentBase.Meta):
        verbose_name = "Culture Pillar"
        verbose_name_plural = "Culture Pillars"

    def __str__(self) -> str:
        return self.title
