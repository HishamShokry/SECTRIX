"""Editable site content.

Everything the public pages render — copy, stats, leadership, timeline — lives
here so it can be maintained from the admin rather than in code.

Field names deliberately match the template variables they replaced, so the
templates did not have to change when this content moved out of
``apps.core.content``.

Admin labels are named "<page> · <section heading>" using the wording that
actually appears on the page, so an editor can find the block they are looking
at without knowing the model names.
"""
from django.core.cache import cache
from django.db import models

from apps.core.icons import (
    ICON_CHOICES,
    SOCIAL_ICON_CHOICES,
    render_icon,
    render_social_icon,
)


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


class SiteSettingsQuerySet(models.QuerySet):
    def delete(self):
        """Block bulk deletion.

        ``Model.delete()`` is only called for single instances, so an override
        there leaves ``SiteSettings.objects.all().delete()`` free to remove the
        row — which silently reverts the site's identity to field defaults.
        """
        raise models.ProtectedError(
            "SiteSettings is a singleton and cannot be deleted.", list(self)
        )


class SiteSettings(models.Model):
    """Site-wide identity and contact details. A single row.

    Replaces the hardcoded ``settings.SITE_META`` dict. Field names match the
    keys that dict used, so ``{{ site.name }}`` and friends still resolve.
    """

    CACHE_KEY = "core.sitesettings"

    objects = SiteSettingsQuerySet.as_manager()

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
        # Singleton: always row 1, so a second row cannot exist. force_insert
        # is dropped so ``objects.create()`` updates row 1 instead of raising
        # an IntegrityError against the existing primary key.
        self.pk = 1
        kwargs.pop("force_insert", None)
        super().save(*args, **kwargs)
        cache.delete(self.CACHE_KEY)

    def delete(self, *args, **kwargs):
        """Refuse deletion; the site needs these values to render.

        Raises rather than returning silently so a caller learns the operation
        was refused instead of assuming it succeeded.
        """
        raise models.ProtectedError(
            "SiteSettings is a singleton and cannot be deleted.", [self]
        )

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
        verbose_name = "Home · Trusted-By Entry"
        verbose_name_plural = "Home · Trusted By"

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
        verbose_name = "Home · Measured Outcome"
        verbose_name_plural = "Home · Measured Outcomes"

    def __str__(self) -> str:
        return f"{self.value}{self.suffix} — {self.label}"


class HomeFeature(ContentBase, IconMixin):
    title = models.CharField(max_length=140)
    body = models.TextField()

    class Meta(ContentBase.Meta):
        verbose_name = "Home · Why Sectrex Card"
        verbose_name_plural = "Home · Why Sectrex"

    def __str__(self) -> str:
        return self.title


class CompanyValue(ContentBase):
    title = models.CharField(max_length=140)
    body = models.TextField()

    class Meta(ContentBase.Meta):
        verbose_name = "About · Value"
        verbose_name_plural = "About · Values"

    def __str__(self) -> str:
        return self.title


class ExpertisePillar(ContentBase):
    tag = models.CharField(max_length=60, help_text="Small mono label above the title.")
    title = models.CharField(max_length=140)
    body = models.TextField()

    class Meta(ContentBase.Meta):
        verbose_name = "About · Expertise Area"
        verbose_name_plural = "About · Expertise"

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
        verbose_name = "About · Leader"
        verbose_name_plural = "About · Leadership"

    def __str__(self) -> str:
        return f"{self.name} — {self.role}"


class TimelineEntry(ContentBase):
    year = models.CharField(max_length=10)
    title = models.CharField(max_length=140)
    body = models.TextField()

    class Meta(ContentBase.Meta):
        verbose_name = "About · Trajectory Entry"
        verbose_name_plural = "About · Trajectory"

    def __str__(self) -> str:
        return f"{self.year} — {self.title}"


class SocialLink(ContentBase):
    """A social profile link in the footer.

    Replaces a hardcoded block, and deliberately does not store markup: the
    icon is chosen by key from a fixed registry, so an editor cannot inject
    HTML into the footer of every page. This is the pattern the earlier
    `{{ net.icon|safe }}` loop got wrong.
    """

    name = models.CharField(max_length=60, help_text="Used as the link's accessible label.")
    url = models.URLField(help_text="Full profile URL, e.g. https://www.linkedin.com/company/…")
    icon_key = models.CharField(
        max_length=40,
        choices=SOCIAL_ICON_CHOICES,
        help_text="Brand mark to display.",
    )

    class Meta(ContentBase.Meta):
        verbose_name = "Footer · Social Link"
        verbose_name_plural = "Footer · Social Links"

    def __str__(self) -> str:
        return self.name

    @property
    def icon(self) -> str:
        """Inline SVG from the registry — never editor-supplied markup."""
        return render_social_icon(self.icon_key)


class CulturePillar(ContentBase):
    tag = models.CharField(max_length=60)
    title = models.CharField(max_length=140)
    body = models.TextField()

    class Meta(ContentBase.Meta):
        verbose_name = "Careers · Culture Pillar"
        verbose_name_plural = "Careers · Culture"

    def __str__(self) -> str:
        return self.title
