from django import forms

from .models import ContactInquiry


_BASE_INPUT = (
    "w-full bg-navy-900/40 border border-white/10 rounded-md px-4 py-3 "
    "text-white placeholder-graphite-300 focus:outline-none focus:border-accent "
    "focus:ring-1 focus:ring-accent transition"
)
_BASE_SELECT = _BASE_INPUT + " appearance-none"
_BASE_TEXTAREA = _BASE_INPUT + " resize-none"


class ContactInquiryForm(forms.ModelForm):
    # Honeypot — bots fill this; humans don't see it.
    website = forms.CharField(required=False, widget=forms.HiddenInput)

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

    def clean_website(self):
        # Honeypot: any value means likely bot.
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Spam detected.")
        return ""

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
