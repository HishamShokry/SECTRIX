import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.crypto import salted_hmac
from django.views.generic.edit import FormView

from .forms import ContactInquiryForm

logger = logging.getLogger(__name__)


def client_ip(request) -> str:
    """Best-effort client address.

    REMOTE_ADDR is the proxy's address once nginx is in front, so every
    visitor would otherwise collapse to one value. nginx overwrites
    X-Forwarded-For, which makes its leftmost entry trustworthy — but only
    when we know we are actually behind that proxy.
    """
    if getattr(settings, "BEHIND_PROXY", False):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def hash_ip(ip: str) -> str:
    """Keyed hash of a client address.

    A bare SHA-256 of an IPv4 address is reversible by exhausting the 2**32
    address space, so it pseudonymises nothing. Keying with SECRET_KEY means
    the mapping cannot be recomputed without the key. Note the result is
    still personal data under GDPR — it is linkable — so it stays subject to
    the same retention rules as the rest of the row.
    """
    if not ip:
        return ""
    return salted_hmac("sectrex.contact.ip", ip, algorithm="sha256").hexdigest()


class ContactView(FormView):
    template_name = "contact/contact.html"
    form_class = ContactInquiryForm
    success_url = reverse_lazy("contact:thanks")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["meta_title"] = "Contact · Sectrex"
        ctx["meta_description"] = (
            "Speak with Sectrex about an engagement, an active incident, or a "
            "strategic security assessment for your organization."
        )
        ctx["offices"] = [
            {
                "city": "Dubai",
                "country": "United Arab Emirates",
                "address": "Dubai Internet City · Building 14 · Dubai, UAE",
                "phone": "+971 4 000 0000",
                "email": "dubai@sectrexconsulting.com",
                "is_headquarters": True,
            },
            {
                "city": "Riyadh",
                "country": "Saudi Arabia",
                "address": "King Abdullah Financial District · Riyadh, KSA",
                "phone": "+966 11 000 0000",
                "email": "riyadh@sectrexconsulting.com",
                "is_headquarters": False,
            },
            {
                "city": "Doha",
                "country": "Qatar",
                "address": "West Bay · Doha, Qatar",
                "phone": "+974 4000 0000",
                "email": "doha@sectrexconsulting.com",
                "is_headquarters": False,
            },
        ]
        return ctx

    def form_valid(self, form):
        inquiry = form.save(commit=False)
        inquiry.user_agent = self.request.META.get("HTTP_USER_AGENT", "")[:400]
        inquiry.ip_hash = hash_ip(client_ip(self.request))
        inquiry.save()

        # Notify the inbox. Errors are logged rather than swallowed: a
        # submitter could otherwise suppress the notification entirely (a
        # newline in a header field raises BadHeaderError), and an SMTP
        # outage would lose inquiries with no operational signal.
        try:
            send_mail(
                subject=f"[Sectrex] New {inquiry.get_interest_display()} inquiry",
                message=(
                    f"From: {inquiry.full_name} <{inquiry.work_email}>\n"
                    f"Company: {inquiry.company}\n"
                    f"Title: {inquiry.job_title}\n"
                    f"Phone: {inquiry.phone}\n"
                    f"Country: {inquiry.country}\n"
                    f"Org size: {inquiry.get_organization_size_display()}\n"
                    f"Interest: {inquiry.get_interest_display()}\n\n"
                    f"Message:\n{inquiry.message}\n"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_INBOX],
                fail_silently=False,
            )
            inquiry.notified_at = timezone.now()
            inquiry.save(update_fields=["notified_at"])
        except Exception:
            # The inquiry is saved either way, so the submitter is not
            # penalised for our mail problem — but we must know about it.
            logger.exception(
                "Contact notification failed for inquiry %s (%s)",
                inquiry.pk,
                inquiry.company,
            )

        messages.success(self.request, "Thank you — a Sectrex specialist will reach out within one business day.")
        return super().form_valid(form)


def thanks(request):
    return render(request, "contact/thanks.html", {
        "meta_title": "Thank you · Sectrex",
        "meta_description": "Your inquiry has been received.",
    })
