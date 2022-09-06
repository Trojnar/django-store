from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.shortcuts import render
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.db.models import Prefetch
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
)

from .models import Category


from accounts.utils.utils import StaffPrivilegesRequiredMixin
from transactions.views import CartView
from products.views import ProductListView
from products.models import get_product_model
from products.views import CheckboxView
from images.models import Image


class CategoryListView(ListView):
    model = Category
    template_name = "category_list.html"
    success_url = reverse_lazy("category_list")
    rows_count = 4

    def get(self, request, *args, **kwargs):
        self.request = request
        return super().get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        category_rows = list()
        row = list()
        for index, object in enumerate(self.object_list):
            row.append(object)
            if ((index + 1) % self.rows_count) == 0:
                category_rows.append(row)
                row = list()

        # Add blank items to row to make last row the same length
        for index in range(
            self.rows_count - (self.object_list.count() % self.rows_count)
        ):
            row.append("blank")
        category_rows.append(row)

        context = super().get_context_data(**kwargs)
        context["category_rows"] = category_rows

        if "category_create" in self.request.POST:
            self.request.method = "GET"
            context["category_create_form"] = CategoryCreateView(
                request=self.request
            ).get_form()
            self.request.method = "POST"
        elif "category_update" in self.request.POST:
            self.request.method = "GET"
            context["category_update_form"] = CategoryUpdateView(
                request=self.request
            ).get_form()
            self.request.method = "POST"
            context["form_pk"] = self.request.POST["category_pk"]
            # Set placeholder text for update form
            context["category_update_form"] = (
                context["category_update_form"]
                .fields["name"]
                .widget.render(
                    "name",
                    context["object_list"]
                    .get(pk=self.request.POST["category_pk"])
                    .name,
                )
            )
        return context

    def post(self, request, *args, **kwargs):
        if "submit_category_create" in self.request.POST:
            CategoryCreateView.as_view()(request)
        elif "category_delete" in self.request.POST:
            CategoryDeleteView.as_view()(request, pk=self.request.POST["category_pk"])
        elif "submit_category_update" in self.request.POST:
            CategoryUpdateView.as_view()(request, pk=self.request.POST["category_pk"])
        elif "category_add_delete_products" in self.request.POST:
            return HttpResponseRedirect(
                reverse(
                    "category_checkbox", kwargs={"pk": self.request.POST["category_pk"]}
                )
            )
        return render(
            request,
            "category_list.html",
            self.get(request, *args, **kwargs).context_data,
        )


class CategoryCreateView(LoginRequiredMixin, StaffPrivilegesRequiredMixin, CreateView):
    model = Category
    template_name = "category_create.html"
    fields = ("name",)


class CategoryDeleteView(LoginRequiredMixin, StaffPrivilegesRequiredMixin, DeleteView):
    model = Category
    success_url = reverse_lazy("category_list")


class CategoryUpdateView(LoginRequiredMixin, StaffPrivilegesRequiredMixin, UpdateView):
    model = Category
    template_name = "category_update.html"
    fields = ("name",)

    def post(self, request, *args, **kwargs):
        self.request = request
        return super().post(request, *args, **kwargs)


class CategoryDetailsView(DetailView):
    model = Category
    template_name = "category_details.html"

    def get_context_data(self, **kwargs):
        # TODO crate funciton to paginate queryset, and get thumbnails
        # use ProductListView context, with category associated products queryset.
        context = super().get_context_data(**kwargs)
        associated_products_context = ProductListView(
            queryset=self.object.products.prefetch_related(
                Prefetch("images", Image.objects.filter(place=0), to_attr="thumbnail")
            ),
            kwargs=kwargs,
            request=self.request,
        ).get_context_data()
        merged_context = {**context, **associated_products_context}
        return merged_context

    def post(self, request, *args, **kwargs):
        if "cart_add_button" in request.POST:
            # add to cart button clicked
            if request.user.is_authenticated:
                cart = request.user.carts.get(transaction=None)
                CartView.as_view()(
                    request, pk=cart.pk, product_pk=request.POST["product_pk"]
                )
        return render(
            request,
            self.template_name,
            self.get(request, *args, **kwargs).context_data,
        )


class CategoryManageProductsView(
    LoginRequiredMixin, StaffPrivilegesRequiredMixin, CheckboxView
):
    model = get_product_model()
    partner_model = Category
    relation_name = "products"
    template_name = "category_checkbox.html"
