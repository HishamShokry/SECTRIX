from django.db import models
from django.utils.text import slugify

from apps.core.icons import ICON_CHOICES, render_icon


class Service(models.Model):
    title = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    short_description = models.CharField(
        max_length=240,
        help_text="One-line summary shown in cards and the home grid.",
    )
    description = models.TextField(help_text="Long-form description for the services page.")
    icon_key = models.CharField(
        max_length=40,
        choices=ICON_CHOICES,
        default="shield",
        help_text="Pick from the built-in icon set.",
    )
    anchor = models.SlugField(
        max_length=80,
        blank=True,
        help_text="In-page anchor used by the services page and home links.",
    )
    tag = models.CharField(
        max_length=60,
        blank=True,
        help_text="Small mono label above the title, e.g. \"01\".",
    )
    intro = models.TextField(
        blank=True, help_text="Opening paragraph on the services page."
    )
    outcome = models.CharField(
        max_length=240, blank=True, help_text="Single-line outcome statement."
    )
    capabilities = models.JSONField(
        default=list,
        blank=True,
        help_text='List of bullet capabilities, e.g. ["24/7 SOC", "MITRE ATT&CK mapped"].',
    )
    display_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "title"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if not self.anchor:
            self.anchor = self.slug
        super().save(*args, **kwargs)

    @property
    def icon(self) -> str:
        """Inline SVG, so templates keep using ``{{ s.icon|safe }}``."""
        return render_icon(self.icon_key)

    @property
    def summary(self) -> str:
        """Alias kept so the home-page teaser template is unchanged."""
        return self.short_description
