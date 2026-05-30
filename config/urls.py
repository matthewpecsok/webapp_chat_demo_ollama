"""URL routing for the project."""
from django.urls import include, path


urlpatterns = [
    path("", include("storefront.urls")),
]
