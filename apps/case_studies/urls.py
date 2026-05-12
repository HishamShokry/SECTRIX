from django.urls import path

from . import views

app_name = "case_studies"

urlpatterns = [
    path("", views.CaseStudyListView.as_view(), name="list"),
]
