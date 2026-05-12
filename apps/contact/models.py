from django.db import models


class ContactInquiry(models.Model):
    INTEREST_CHOICES = [
        ("threat_detection", "Threat Detection & Response"),
        ("cloud_security", "Cloud Security"),
        ("infrastructure", "Infrastructure Protection"),
        ("incident_response", "Incident Response"),
        ("zero_trust", "Zero Trust Architecture"),
        ("consulting", "Security Consulting"),
        ("partnership", "Partnership / Alliance"),
        ("general", "General Inquiry"),
    ]

    ORG_SIZE_CHOICES = [
        ("1_50", "1 – 50 employees"),
        ("51_500", "51 – 500 employees"),
        ("501_2000", "501 – 2,000 employees"),
        ("2001_10000", "2,001 – 10,000 employees"),
        ("10001_plus", "10,001+ employees"),
    ]

    full_name = models.CharField(max_length=120)
    work_email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    company = models.CharField(max_length=160)
    job_title = models.CharField(max_length=120, blank=True)
    country = models.CharField(max_length=80, blank=True)
    organization_size = models.CharField(max_length=20, choices=ORG_SIZE_CHOICES, blank=True)
    interest = models.CharField(max_length=40, choices=INTEREST_CHOICES, default="general")
    message = models.TextField()

    # Lifecycle
    created_at = models.DateTimeField(auto_now_add=True)
    is_handled = models.BooleanField(default=False)
    handled_by = models.CharField(max_length=120, blank=True)
    internal_notes = models.TextField(blank=True)

    # Light spam control
    user_agent = models.CharField(max_length=400, blank=True)
    ip_hash = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Contact Inquiry"
        verbose_name_plural = "Contact Inquiries"

    def __str__(self) -> str:
        return f"{self.full_name} · {self.company} ({self.get_interest_display()})"
