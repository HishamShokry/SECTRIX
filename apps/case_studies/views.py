from django.views.generic import ListView

from .models import CaseStudy


class CaseStudyListView(ListView):
    model = CaseStudy
    template_name = "case_studies/list.html"
    context_object_name = "case_studies"
    paginate_by = 12

    def get_queryset(self):
        return CaseStudy.objects.filter(is_published=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["meta_title"] = "Case Studies · Sectrix"
        ctx["meta_description"] = (
            "Selected engagements with Gulf banks, sovereign agencies, and "
            "regional enterprises — measurable outcomes from Sectrix "
            "cybersecurity programs."
        )
        ctx["sectors"] = CaseStudy.SECTOR_CHOICES
        return ctx
