from django.views.generic import TemplateView

from apps.core import content


class ServiceListView(TemplateView):
    """Static-rendered services page.

    The Service DB model exists for admin-managed additions and future detail
    pages; the canonical six service offerings are rendered from
    ``apps.core.content.SERVICE_DETAIL`` so the page always renders correctly
    with rich icons and copywriting and editors only edit one file.
    """

    template_name = "services/list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["services"] = content.SERVICE_DETAIL
        ctx["meta_title"] = "Services · Sectrex"
        ctx["meta_description"] = (
            "Enterprise cybersecurity services — threat detection, cloud "
            "security, infrastructure protection, incident response, zero "
            "trust architecture, and security consulting."
        )
        return ctx
