from django.shortcuts import render

from django.views.generic import TemplateView


class HomePageView(TemplateView):
    template_name = "pages/home.html"


class HomePageEditPropertiesView(TemplateView):
    template_name = "pages/home_properties.html"
    # TODO: homepage management
    # * categories to display on main page
    # * images display on main page on carousel

    def post(self, request, *args, **kwargs):
        print(1)
        return super().post(self, request, args, kwargs)
