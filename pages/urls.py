from django.urls import path
from .views import HomePageView, HomePagePropertiesView

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path(
        "homepage_properties/",
        HomePagePropertiesView.as_view(),
        name="homepage_properties",
    ),
]
