import hashlib

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic.edit import FormView

from .forms import ContactInquiryForm


class ContactView(FormView):
    template_name = "contact/contact.html"
    form_class = ContactInquiryForm
    success_url = reverse_lazy("contact:thanks")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["meta_title"] = "Contact · Sectrix"
        ctx["meta_description"] = (
            "Speak with Sectrix about an engagement, an active incident, or a "
            "strategic security assessment for your organization."
        )
        ctx["offices"] = [
            {
                "city": "Dubai",
                "country": "United Arab Emirates",
                "address": "Dubai Internet City · Building 14 · Dubai, UAE",
                "phone": "+971 4 000 0000",
                "email": "dubai@sectrix.com",
                "is_headquarters": True,
            },
            {
                "city": "Riyadh",
                "country": "Saudi Arabia",
                "address": "King Abdullah Financial District · Riyadh, KSA",
                "phone": "+966 11 000 0000",
                "email": "riyadh@sectrix.com",
                "is_headquarters": False,
            },
            {
                "city": "Doha",
                "country": "Qatar",
                "address": "West Bay · Doha, Qatar",
                "phone": "+974 4000 0000",
                "email": "doha@sectrix.com",
                "is_headquarters": False,
            },
        ]
        return ctx

    def form_valid(self, form):
        inquiry = form.save(commit=False)
        inquiry.user_agent = self.request.META.get("HTTP_USER_AGENT", "")[:400]
        ip = self.request.META.get("REMOTE_ADDR", "")
        if ip:
            inquiry.ip_hash = hashlib.sha256(ip.encode()).hexdigest()
        inquiry.save()

        # Notify inbox; backend defaults to console in dev (see settings).
        try:
            send_mail(
                subject=f"[Sectrix] New inquiry — {inquiry.company} ({inquiry.get_interest_display()})",
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
                fail_silently=True,
            )
        except Exception:
            pass

        messages.success(self.request, "Thank you — a Sectrix specialist will reach out within one business day.")
        return super().form_valid(form)


def thanks(request):
    return render(request, "contact/thanks.html", {
        "meta_title": "Thank you · Sectrix",
        "meta_description": "Your inquiry has been received.",
    })
