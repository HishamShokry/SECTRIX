from django.db import models
from django.utils.text import slugify


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
        default="shield",
        help_text="Icon identifier — matched in templates/partials/icons.html.",
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
        super().save(*args, **kwargs)
