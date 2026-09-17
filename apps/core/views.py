from django.shortcuts import render
from django.views.generic import TemplateView

from apps.case_studies.models import CaseStudy
from apps.services.models import Service

from .models import (
    CompanyValue,
    ExpertisePillar,
    HomeFeature,
    HomeStat,
    LeadershipMember,
    TimelineEntry,
    TrustedByLogo,
)


class HomeView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        services = Service.objects.filter(is_published=True)[:6]
        ctx["services"] = services
        ctx["case_studies"] = CaseStudy.objects.filter(is_published=True)[:3]

        # All section copy is admin-editable; see apps.core.models.
        ctx["trusted_by"] = TrustedByLogo.objects.live()
        ctx["default_services"] = services
        ctx["stats"] = HomeStat.objects.live()
        ctx["features"] = HomeFeature.objects.live()

        ctx["meta_title"] = "Sectrex · Enterprise Cybersecurity"
        ctx["meta_description"] = (
            "Sectrex delivers enterprise-grade cybersecurity for Gulf banks, "
            "governments, and large organizations. Threat detection, cloud "
            "security, zero trust, and incident response."
        )
        return ctx


class AboutView(TemplateView):
    template_name = "core/about.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["values"] = CompanyValue.objects.live()
        ctx["expertise"] = ExpertisePillar.objects.live()
        ctx["leadership"] = LeadershipMember.objects.live()
        ctx["timeline"] = TimelineEntry.objects.live()

        ctx["meta_title"] = "About · Sectrex"
        ctx["meta_description"] = (
            "Sectrex is an enterprise cybersecurity partner founded on the "
            "principle that defense must be engineered with the same rigor as "
            "the systems it protects."
        )
        return ctx


def handler404(request, exception):
    return render(request, "404.html", status=404)


def handler500(request):
    return render(request, "500.html", status=500)
