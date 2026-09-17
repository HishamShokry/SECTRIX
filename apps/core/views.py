from django.shortcuts import render
from django.views.generic import TemplateView

from apps.case_studies.models import CaseStudy
from apps.services.models import Service

from . import content


class HomeView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["services"] = Service.objects.filter(is_published=True)[:6]
        ctx["case_studies"] = CaseStudy.objects.filter(is_published=True)[:3]

        # Marketing content for hero/sections — kept in core.content so the
        # template stays presentational and copy is editable in one place.
        ctx["trusted_by"] = content.TRUSTED_BY
        ctx["default_services"] = content.SERVICE_TEASERS
        ctx["stats"] = content.HOME_STATS
        ctx["features"] = content.HOME_FEATURES

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
        ctx["values"] = content.COMPANY_VALUES
        ctx["expertise"] = content.EXPERTISE_PILLARS
        ctx["leadership"] = content.LEADERSHIP
        ctx["timeline"] = content.TIMELINE

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
