from django.urls import path

from . import views

app_name = "careers"

urlpatterns = [
    path("", views.CareersView.as_view(), name="list"),
]
