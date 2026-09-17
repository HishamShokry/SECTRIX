import time

from django import forms
from django.core import signing

from .models import ContactInquiry


_BASE_INPUT = (
    "w-full bg-navy-900/40 border border-white/10 rounded-md px-4 py-3 "
    "text-white placeholder-graphite-300 focus:outline-none focus:border-accent "
    "focus:ring-1 focus:ring-accent transition"
)
_BASE_SELECT = _BASE_INPUT + " appearance-none"
_BASE_TEXTAREA = _BASE_INPUT + " resize-none"


class ContactInquiryForm(forms.ModelForm):
    # Honeypot — bots fill this; humans don't see it. Rendered off-screen by
    # CSS rather than as type=hidden, so a scripted client that only submits
    # visible inputs still trips it.
    website = forms.CharField(
        required=False,
        label="Website",
        widget=forms.TextInput(attrs={
            "class": "hp-field",
            "tabindex": "-1",
            "autocomplete": "off",
            "aria-hidden": "true",
        }),
    )
    # Signed render timestamp: proves the form was actually fetched, and how
    # long ago. Signed so it cannot be back-dated by the client.
    rendered_at = forms.CharField(required=False, widget=forms.HiddenInput)

    #: Submissions faster than this are treated as automated. Kept low so a
    #: fast human using browser autofill is not caught; a rejected submission
    #: shows a visible error and succeeds on retry, because the signed
    #: timestamp is preserved across the redisplay.
    MIN_FILL_SECONDS = 2

    class Meta:
        model = ContactInquiry
        fields = [
            "full_name",
            "work_email",
            "phone",
            "company",
            "job_title",
            "country",
            "organization_size",
            "interest",
            "message",
        ]
        widgets = {
            "full_name":         forms.TextInput(attrs={"class": _BASE_INPUT,    "placeholder": "Jane Al-Mansoori"}),
            "work_email":        forms.EmailInput(attrs={"class": _BASE_INPUT,   "placeholder": "jane@yourcompany.com"}),
            "phone":             forms.TextInput(attrs={"class": _BASE_INPUT,    "placeholder": "+971 50 000 0000"}),
            "company":           forms.TextInput(attrs={"class": _BASE_INPUT,    "placeholder": "Your organization"}),
            "job_title":         forms.TextInput(attrs={"class": _BASE_INPUT,    "placeholder": "Head of Information Security"}),
            "country":           forms.TextInput(attrs={"class": _BASE_INPUT,    "placeholder": "United Arab Emirates"}),
            "organization_size": forms.Select(attrs={"class": _BASE_SELECT}),
            "interest":          forms.Select(attrs={"class": _BASE_SELECT}),
            "message":           forms.Textarea(attrs={"class": _BASE_TEXTAREA, "rows": 5, "placeholder": "Tell us about your environment and what you'd like to discuss."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.fields["rendered_at"].initial = signing.dumps(time.time())

    def clean_website(self):
        # Honeypot: any value means likely bot. Raised as a non-field error so
        # a false positive is actually visible to the person filling the form.
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Spam detected.")
        return ""

    def clean_rendered_at(self):
        """Reject submissions that arrive implausibly fast.

        Missing or unreadable values are allowed through: the goal is to raise
        the cost of automation, not to break the form for anyone whose session
        or clock misbehaves.
        """
        raw = self.cleaned_data.get("rendered_at")
        if not raw:
            return ""
        try:
            started = signing.loads(raw, max_age=60 * 60 * 6)
        except signing.BadSignature:
            return ""
        if time.time() - float(started) < self.MIN_FILL_SECONDS:
            raise forms.ValidationError("Spam detected.")
        return raw

    def add_error(self, field, error):
        """Surface honeypot/timing rejections where the template renders them."""
        if field in {"website", "rendered_at"}:
            field = None
        super().add_error(field, error)

    def clean_work_email(self):
        email = self.cleaned_data["work_email"].lower().strip()
        # Soft-block common free providers for enterprise inquiries.
        free_domains = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com"}
        domain = email.split("@", 1)[-1]
        if domain in free_domains:
            raise forms.ValidationError(
                "Please use a work email address. For general inquiries, "
                "reach us at contact@sectrexconsulting.com."
            )
        return email
