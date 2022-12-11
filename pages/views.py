from itertools import chain
import json
from django.shortcuts import render

from django.views.generic import TemplateView
from accounts.utils.utils import StaffPrivilegesRequiredMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, DeleteView, UpdateView, ListView
from django.urls import reverse_lazy, reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.forms import Form

from categories.models import Category
from .models import HomepageCategory
from categories.views import CategoryListView
from .forms import DisplayCategoryChoiceForm


class HomePageView(TemplateView):
    template_name = "pages/home.html"


class HomePagePropertiesView(
    LoginRequiredMixin, StaffPrivilegesRequiredMixin, TemplateView
):
    template_name = "pages/home_properties.html"
    # TODO: homepage management
    # * categories to display on main page
    # * images display on main page in carousel

    def get(self, request, *args, **kwargs):
        try:
            with open("./pages/json/homepage_structure.json", "r") as f:
                seen = json.load(f)
        except:
            seen = dict()

        create_form = HomepageCategoryCreateView().get_form_class()
        context = self.get_context_data(**kwargs)
        context["create_homepage_category_form"] = create_form

        # categories
        category_list = CategoryListView.as_view()(request)
        category_list = category_list.context_data["object_list"]

        category_list = map(
            lambda x: (x.id, x.name),
            filter(
                lambda x: False if [str(type(x)), x.id] in seen.values() else True,
                category_list,
            ),
        )

        categories = list(category_list)

        categories_form = DisplayCategoryChoiceForm(choices=categories)

        context["categories_form"] = categories_form

        # homepage categories
        hmpg_category_list = HomepageCategoryListView.as_view()(request)
        hmpg_category_list = hmpg_category_list.context_data["object_list"]

        hmpg_category_list = map(
            lambda x: (x.id, x.name),
            filter(lambda x: False if x in seen.keys() else True, hmpg_category_list),
        )

        hmpg_categories = list(hmpg_category_list)

        hmpg_categories_form = DisplayCategoryChoiceForm(choices=hmpg_categories)

        context["hmpg_categories_form"] = hmpg_categories_form

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):

        if "submit_homepage_category_create" in request.POST:
            HomepageCategoryCreateView.as_view()(request)
        if "categories_display_button" in request.POST:
            try:
                with open("./pages/json/homepage_structure.json", "r") as file:
                    structure = json.load(file)
            except FileNotFoundError:
                structure = {}

            category_ids = request.POST.getlist("categories")
            queryset = Category.objects.filter(id__in=category_ids)
            # every category in order list(homepage_structure.json) is saved as
            # "position" = (type of object, id)
            position = dict()
            for i, category in enumerate(queryset):
                position[len(structure) + i] = (str(type(category)), category.id)
            structure = structure | position

            with open("./pages/json/homepage_structure.json", "w") as file:
                json.dump(structure, file, indent=4)
        if "hmpg_categories_display_button" in request.POST:
            with json.open("homepage_structure.json", "r") as file:
                structure = json.load(file)
            for category in request.POST.getlist("categories"):
                print(category)
        return HttpResponseRedirect(reverse("homepage_properties"))


class HomepageCategoryCreateView(
    LoginRequiredMixin, StaffPrivilegesRequiredMixin, CreateView
):
    model = HomepageCategory
    template_name = "homepage_category_create.html"
    fields = ("name",)
    success_url = reverse_lazy("home")


class CategoryDeleteView(LoginRequiredMixin, StaffPrivilegesRequiredMixin, DeleteView):
    model = HomepageCategory
    success_url = reverse_lazy("homepage_category_list")


class CategoryUpdateView(LoginRequiredMixin, StaffPrivilegesRequiredMixin, UpdateView):
    model = HomepageCategory
    template_name = "homepage_category_update.html"
    fields = ("name",)

    def post(self, request, *args, **kwargs):
        self.request = request
        return super().post(request, *args, **kwargs)


class HomepageCategoryListView(ListView):
    model = HomepageCategory
    template_name = "category_list.html"
    success_url = reverse_lazy("home")
