from django.views.generic import ListView

from .models import Service


class ServiceListView(ListView):
    """Services page, rendered from admin-managed Service records."""

    model = Service
    template_name = "services/list.html"
    context_object_name = "services"

    def get_queryset(self):
        return Service.objects.filter(is_published=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["meta_title"] = "Services · Sectrex"
        ctx["meta_description"] = (
            "Enterprise cybersecurity services — threat detection, cloud "
            "security, infrastructure protection, incident response, zero "
            "trust architecture, and security consulting."
        )
        return ctx
