import uuid
from pathlib import Path

from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.text import slugify

from apps.core.validators import validate_string_list

ALLOWED_IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]


def case_study_image_path(instance, filename: str) -> str:
    """Store under a generated name.

    ImageField validates that the *content* parses as an image but not the
    extension, so a valid image byte stream named ``payload.html`` would be
    written verbatim and, wherever media is served, returned as text/html
    from this origin. Discarding the submitted name removes that entirely.
    """
    suffix = Path(filename).suffix.lower()
    if suffix.lstrip(".") not in ALLOWED_IMAGE_EXTENSIONS:
        suffix = ".jpg"
    return f"case_studies/{uuid.uuid4().hex}{suffix}"


class CaseStudy(models.Model):
    SECTOR_CHOICES = [
        ("banking", "Banking & Financial Services"),
        ("government", "Government & Public Sector"),
        ("energy", "Energy & Utilities"),
        ("healthcare", "Healthcare"),
        ("telecom", "Telecommunications"),
        ("retail", "Retail & E-commerce"),
        ("logistics", "Logistics & Transportation"),
    ]

    title = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    client_name = models.CharField(
        max_length=120,
        help_text='Client name or "Confidential — Tier-1 Bank" when under NDA.',
    )
    sector = models.CharField(max_length=40, choices=SECTOR_CHOICES)
    region = models.CharField(max_length=80, default="GCC")
    summary = models.CharField(max_length=280, help_text="Card summary.")
    challenge = models.TextField()
    approach = models.TextField()
    outcome = models.TextField()
    headline_metric = models.CharField(
        max_length=40,
        blank=True,
        help_text='Hero number, e.g. "99.97%" or "−72%".',
    )
    headline_metric_label = models.CharField(
        max_length=80,
        blank=True,
        help_text='Label for the hero metric, e.g. "Reduction in mean time to detect".',
    )
    cover_image = models.ImageField(
        upload_to=case_study_image_path,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(ALLOWED_IMAGE_EXTENSIONS)],
    )
    tags = models.JSONField(default=list, blank=True, validators=[validate_string_list])
    is_published = models.BooleanField(default=True)
    published_at = models.DateField(null=True, blank=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "-published_at"]
        verbose_name = "Case Study"
        verbose_name_plural = "Case Studies"

    def __str__(self) -> str:
        return f"{self.client_name} — {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.client_name}-{self.title}")[:180]
        super().save(*args, **kwargs)