from django.db import models
from django.utils.text import slugify


class JobOpening(models.Model):
    DEPARTMENT_CHOICES = [
        ("soc", "Security Operations"),
        ("threat_intel", "Threat Intelligence"),
        ("cloud", "Cloud Security"),
        ("offensive", "Offensive Security"),
        ("engineering", "Platform Engineering"),
        ("grc", "Governance, Risk & Compliance"),
        ("sales", "Enterprise Sales"),
        ("operations", "Operations"),
    ]

    EMPLOYMENT_TYPES = [
        ("full_time", "Full-time"),
        ("contract", "Contract"),
        ("intern", "Internship"),
    ]

    LEVEL_CHOICES = [
        ("junior", "Junior"),
        ("mid", "Mid-level"),
        ("senior", "Senior"),
        ("principal", "Principal"),
        ("lead", "Lead / Manager"),
    ]

    title = models.CharField(max_length=140)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    department = models.CharField(max_length=40, choices=DEPARTMENT_CHOICES)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES, default="full_time")
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default="mid")
    location = models.CharField(max_length=120, default="Dubai, UAE")
    is_remote_friendly = models.BooleanField(default=False)
    summary = models.CharField(max_length=240)
    description = models.TextField()
    requirements = models.JSONField(default=list, blank=True)
    nice_to_have = models.JSONField(default=list, blank=True)
    is_published = models.BooleanField(default=True)
    posted_at = models.DateField(auto_now_add=True)
    closes_at = models.DateField(null=True, blank=True)
    apply_email = models.EmailField(default="careers@sectrix.com")

    class Meta:
        ordering = ["-posted_at", "title"]
        verbose_name = "Job Opening"
        verbose_name_plural = "Job Openings"

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
