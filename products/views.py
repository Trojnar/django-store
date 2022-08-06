from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import ListView, DetailView, TemplateView, CreateView
from django.db.models import Prefetch
from django.contrib.auth.mixins import (
    PermissionRequiredMixin,
    UserPassesTestMixin,
    LoginRequiredMixin,
)
from django import forms

from .models import Product
from .forms import ProductForm
from reviews.models import Review
from reviews.views import CreateReviewView

# from django.contrib.auth.mixins import PermissionRequiredMixin
from itertools import chain


class ProductListView(ListView):
    model = Product
    template_name = "product_list.html"


class ProductDetailsView(DetailView):
    model = Product
    template_name = "product_details.html"

    def get_object(self, queryset=None):
        """Optimize sql query for reviews"""
        queryset = Product.objects.prefetch_related(
            Prefetch("reviews", Review.objects.select_related("author"))
        )
        return super().get_object(queryset)

    def post(self, request, *args, **kwargs):
        """Create review using CreateReviewView instance"""
        view = CreateReviewView()
        view.request = request
        return view.post(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["new_review"] = "You can enter your review here. "
        context["reviews"] = self.object.reviews
        return context


class SearchResultView(TemplateView):
    template_name = "search_result.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        phrase = self.request.GET.get("phrase", None)
        if phrase:
            queryset = self.search(phrase)
            context["search_result"] = queryset

        return context

    def search(self, phrase):
        # Dictionary with field names to search in and priority rate as keys and list
        # to store matches. Priority of search result display is sum of sum of matches
        # in fields. Sum in fields is multiplied by priority rate.
        fields = {("name", 1.0): [], ("producer", 1.2): []}

        for word in phrase.split():
            for key in fields.keys():
                fields[key].append(
                    Product.objects.all().filter(**{f"{key[0]}__icontains": word})
                )

        # Count match for each field, replace matches in fields dict to matches count.
        # Count is multiplied by priority rate.
        for key in fields.keys():
            temp_dict = {}
            result_l = list(chain.from_iterable(fields[key]))
            for result in result_l:
                temp_dict[result] = result_l.count(result) * key[1]
            fields[key] = temp_dict

        # Sum of counts for each object.
        result = {}
        for queryset in fields.values():
            for key, value in queryset.items():
                if key in result:
                    result[key] += value
                else:
                    result[key] = value

        # sorting dictionary by value
        sorted_tuples = sorted(result.items(), key=lambda item: item[1], reverse=True)
        sorted_dict = {k: v for k, v in sorted_tuples}

        return sorted_dict.keys()


class CreateProductView(PermissionRequiredMixin, CreateView):
    model = Product
    template_name = "product_create.html"
    permission_required = "products.add_product"
    form_class = ProductForm


class EditProductDetailsView(
    LoginRequiredMixin, UserPassesTestMixin, ProductDetailsView
):
    editable = (
        "name",
        "producer",
        "price",
    )

    def get(self, request, *args, **kwargs):
        # Pass get's 'edit' value to instance variable self.edit.

        if kwargs["edit"] in self.editable:
            self.edit = kwargs["edit"]

        return super().get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["new_review"] = "You can enter your review here. "

        # Change field in product dict, choosen by get's variable self.edit,
        # to form's widget. Pass it to the context.
        form = ProductForm()
        product_dict = forms.model_to_dict(self.object)
        product_dict["pk"] = self.object.pk
        product_dict[self.edit] = form.fields[self.edit].widget.render(
            self.edit, product_dict[self.edit]
        )
        context["product"] = product_dict
        context["reviews"] = self.object.reviews
        context["edit"] = self.edit

        return context

    def post(self, request, *args, **kwargs):
        # Get product and choosen field to edit from get, get post data, create dict
        # with product details, create form and validate input. Override database data
        # in choosen kwargs["edit"] field.
        self.object = Product.objects.get(pk=kwargs["pk"])
        input = request.POST[kwargs["edit"]]
        edit = kwargs["edit"]
        if edit in self.editable:
            product_dict = forms.model_to_dict(self.object)
            product_dict[edit] = input
            form = ProductForm(product_dict)
            if form.is_valid():
                new_record = form.save(commit=False)
                exec("self.object." + edit + " = " + "new_record." + edit)
                self.object.save()
            return HttpResponseRedirect(
                reverse("product_details", kwargs={"pk": kwargs["pk"]})
            )
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def test_func(self):
        return self.request.user.is_staff
