from django.views.generic import ListView

from apps.core.models import CulturePillar

from .models import JobOpening


class CareersView(ListView):
    model = JobOpening
    template_name = "careers/list.html"
    context_object_name = "jobs"

    def get_queryset(self):
        return JobOpening.objects.filter(is_published=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["meta_title"] = "Careers · Sectrex"
        ctx["meta_description"] = (
            "Join Sectrex — build the next generation of cybersecurity "
            "defense for Gulf enterprises. Open roles across SOC, threat "
            "intelligence, cloud security, and offensive security."
        )
        ctx["departments"] = JobOpening.DEPARTMENT_CHOICES
        ctx["culture_pillars"] = CulturePillar.objects.live()
        return ctx
