from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.shortcuts import render
from django.views.generic import (
    ListView,
    DetailView,
    TemplateView,
    CreateView,
    UpdateView,
    FormView,
    DeleteView,
)
from django.db.models import Prefetch
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
)
from django import forms

from .models import Product, Image
from categories.models import Category
from .forms import (
    ImagesManagerForm,
    ProductForm,
    ProductFormWithImage,
    ImageForm,
    ImagesManagerUploadImageForm,
    CheckboxForm,
)
from reviews.forms import ReviewForm
from reviews.models import Review
from reviews.views import CreateReviewView
from accounts.views import StaffPrivilegesRequiredMixin
from transactions.views import CartView


from itertools import chain


class ProductListView(ListView):
    model = Product
    template_name = "product_list.html"
    ordering = "name"
    rows_count = 4
    paginate_by_row = 5
    queryset = Product.objects.prefetch_related(
        Prefetch("images", Image.objects.filter(place=0), to_attr="thumbnail")
    )

    def get_context_data(self, **kwargs):
        """split product to rows to display them on page, and add thumbnail
        (product, thumbnail) for self.rows_count in row"""
        product_rows = list()
        row = list()
        queryset = self.get_queryset()

        for index, object in enumerate(queryset):
            if object.thumbnail:
                # There should be queryset with only one product, because of filter in
                # prefetch, so record of index 0 should be only one possible.
                thumbnail = object.thumbnail[0]
                row.append((object, thumbnail))
            else:
                row.append((object, "no thumbnail"))

            # Add row every self.rows_count'th iteration
            if ((index + 1) % self.rows_count) == 0:
                product_rows.append(row)
                row = list()

        # Add blank items to row to make last row the same length
        for index in range(self.rows_count - (queryset.count() % self.rows_count)):
            row.append(("blank", "no thumbnail"))
        product_rows.append(row)
        return super().get_context_data(object_list=product_rows, **kwargs)

    def get_paginate_by(self, queryset):
        """Get the number of rows to paginate."""
        return self.paginate_by_row

    def post(self, request, *args, **kwargs):
        if "cart_add_button" in request.POST:
            self.cart_add_button(request)
        return HttpResponseRedirect(reverse("product_list"))

    def cart_add_button(self, request):
        if request.user.is_authenticated:
            cart = request.user.carts.get(transaction=None)
            CartView.as_view()(
                request, pk=cart.pk, product_pk=request.POST["product_pk"]
            )


# TODO make it look like CategoryListView or just make custom form
class ProductDetailsView(DetailView):
    model = Product
    template_name = "product_details.html"

    def get_object(self, queryset=None):
        # Optimize sql query for reviews
        queryset = Product.objects.prefetch_related(
            Prefetch("reviews", Review.objects.select_related("author"))
        )
        return super().get_object(queryset)

    def post(self, request, *args, **kwargs):
        """Create review using CreateReviewView instance"""

        if "cart_add_button" in request.POST:
            cart = request.user.carts.get(transaction=None)
            CartView.as_view()(request, pk=cart.pk, product_pk=kwargs["pk"])
        if "review_add_button" in request.POST:
            view = CreateReviewView()
            view.request = self.request
            return view.post(request, *args, **kwargs)
        return HttpResponseRedirect(
            reverse("product_details", kwargs={"pk": kwargs["pk"]})
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["new_review"] = "You can enter your review here. "
        context["reviews"] = self.object.reviews.all()
        context["images"] = ImageManagerView.get_sorted_images(self, self.object)
        return context


class ProductCreateView(StaffPrivilegesRequiredMixin, CreateView):
    model = Product
    template_name = "product_create.html"
    form_class = ProductFormWithImage
    # TODO categories_form = ProductAssignCategoriesView

    def post(self, request, *args, **kwargs):
        # Save images if provided.
        form = self.get_form()
        if form.is_valid():
            self.object = form.save()
            data = {"product": self.object}
            files = request.FILES
            data_plus_files = {"data": data, "files": files}
            image_form = ImageForm(**data_plus_files)
            if image_form.is_valid():
                for index, image in enumerate(files.getlist("image")):
                    Image.objects.create(product=self.object, image=image, place=index)
            elif image_form.is_bound:
                form.add_error(None, image_form.errors["image"])
                return super().form_invalid(form)
            return self.form_valid(form)
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Set object list for CheckboxView get_context_data method's purpose.
        self.object_list = Category.objects.all()
        # Get checbox form from Product's categories manager.
        checkbox_view_context = ProductAssignCategoriesView(
            object_list=self.object_list
        ).get_context_data(**kwargs)
        context.update(checkbox_view_context)
        return context

    def form_valid(self, form):
        """
        If the form is valid, save the product, and assign it to choosen categories.
        """
        self.object = form.save()
        ProductAssignCategoriesView.as_view()(self.request, pk=self.object.pk)
        return super().form_valid(form)


class ProductUpdateView(StaffPrivilegesRequiredMixin, UpdateView):
    model = Product
    template_name = "product_create.html"
    from_class = ProductFormWithImage
    fields = ("name", "producer", "price", "image")


# Images
class ImagesUpload(StaffPrivilegesRequiredMixin, FormView):
    """View that provides uploading images feature."""

    form_class = ImagesManagerUploadImageForm
    template_name = "upload_images.html"

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        images = request.FILES.getlist("image")
        if form.is_valid():
            product = Product.objects.get(pk=self.initial["product_pk"])
            images_queryset = product.images.all()
            for index, image in enumerate(images):
                Image.objects.create(
                    product=product,
                    image=image,
                    place=index
                    + len(images_queryset),  # set diplay position at the end of list
                )
        else:
            print(form.errors)
            # TODO handle error messages| form invalid here
            pass
        return HttpResponseRedirect(self.success_url)


class ImageDeleteView(StaffPrivilegesRequiredMixin, DeleteView):
    """View that provides deleting images feature."""

    model = Image
    success_url = reverse_lazy("product_list")

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        self.fix_image_places(product_pk=request.POST["product_pk"])
        return response

    def fix_image_places(self, product_pk=None):
        """Fix places after image is deleted"""
        if product_pk is None:
            raise ValueError("product_pk can't be None value.")

        images = Product.objects.get(pk=product_pk).images.all()
        for index, image in enumerate(images):
            image.place = index
            image.save()


class ImageManagerView(StaffPrivilegesRequiredMixin, FormView):
    """View that provides managing images feature for product."""

    template_name = "images_manager.html"
    form_class = ImagesManagerForm

    def get(self, request, *args, **kwargs):
        product = Product.objects.get(pk=kwargs["pk"])
        return self.render_to_response(self.get_context_data(**kwargs))

    def get_context_data(self, **kwargs):
        product = Product.objects.get(pk=kwargs["pk"])
        images = self.get_sorted_images(product)

        kwargs["upload_images_form"] = ImagesUpload(
            request=self.request,
            initial={"product_pk": product.pk},
        ).get_context_data()["form"]

        if images:
            # Display images
            # super().get_context_data needs initial to make first form
            self.initial = {"image_pk": images[0].pk, "product_pk": kwargs["pk"]}
            context = super().get_context_data(**kwargs)
            # Initializaition of the first form happened in super().get_context_data
            context["images"] = dict()
            context["images"][images[0]] = context["form"]
            for image in images[1:]:
                initial = {"image_pk": image.pk, "product_pk": kwargs["pk"]}
                form = ImagesManagerForm(initial=initial)
                context["images"][image] = form

            return context

        return kwargs

    def get_initial(self):
        """Return the initial data to use for forms on this view."""
        return self.initial

    def post(self, request, *args, **kwargs):
        if "delete" in request.POST:
            # Deleting files using ImagesDeleteView.
            ImageDeleteView.as_view()(request, pk=request.POST["image_pk"])
        elif "move_up" in request.POST:
            # Changes image display position to higher.
            images = self.get_sorted_images(kwargs["pk"])
            image = images.get(pk=request.POST["image_pk"])
            image.place -= 1
            image.place = self.adjust_index_to_range(0, images.count() - 1, image.place)
            if image.place >= 0:
                next_image = images.get(place=image.place)
                next_image.place += 1
                next_image.place = self.adjust_index_to_range(
                    0, images.count() - 1, next_image.place
                )
                next_image.save()
                image.save()
        elif "move_down" in request.POST:
            # Changes image display position to lower.
            images = self.get_sorted_images(kwargs["pk"])
            image = images.get(pk=request.POST["image_pk"])
            image.place += 1
            image.place = self.adjust_index_to_range(0, images.count() - 1, image.place)
            if image.place < images.count():
                previous_image = images.get(place=image.place)
                previous_image.place -= 1
                previous_image.place = self.adjust_index_to_range(
                    0, images.count() - 1, previous_image.place
                )
                previous_image.save()
                image.save()
        elif "upload_images" in request.POST:
            # Uploading files using ImagesUploadView.
            ImagesUpload.as_view(
                success_url=reverse("images_manager", kwargs={"pk": kwargs["pk"]}),
                initial={"product_pk": kwargs["pk"]},
            )(self.request)
        return HttpResponseRedirect(
            reverse("images_manager", kwargs={"pk": kwargs["pk"]})
        )

    def get_sorted_images(self, product):
        return Image.objects.filter(product=product).order_by("place")

    def adjust_index_to_range(self, start, end, index):
        if index > end:
            index = end
        elif index < start:
            index = 0
        return index


# Products


class EditProductDetailsView(
    LoginRequiredMixin, StaffPrivilegesRequiredMixin, ProductDetailsView
):
    editables = (
        "name",
        "producer",
        "price",
    )

    def get(self, request, *args, **kwargs):
        # Pass get's 'edit' value to instance variable self.edit. If no variable
        # set self.edit to false.
        try:
            self.edit = kwargs["edit"]  # setdefault
            try:
                self.index = kwargs["index"]
            except KeyError:
                pass
        except KeyError:
            self.edit = False

        return super().get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["new_review"] = "You can enter your review here. "

        # Change field in product dict choosen by get's variable self.edit,
        # into form's widget. Pass it to the context.
        if self.edit and self.edit in self.editables:
            form = ProductForm()
            product_dict = forms.model_to_dict(self.object)
            product_dict["pk"] = self.object.pk
            form.fields[self.edit].widget.attrs.update(
                size=len(str(product_dict[self.edit]))
            )
            product_dict[self.edit] = form.fields[self.edit].widget.render(
                self.edit, product_dict[self.edit]
            )
            context["product"] = product_dict
            context["reviews"] = self.object.reviews.all()
            context["edit"] = self.edit

        return context

    def post(self, request, *args, **kwargs):
        # Get product and choosen field to edit from get, get post data, create dict
        # with product details, create form and validate input. Override database data
        # in choosen kwargs["edit"] field.
        try:
            edit = kwargs["edit"]
        except KeyError:
            edit = False

        if edit and edit in self.editables:
            self.object = Product.objects.get(pk=kwargs["pk"])
            input = request.POST[kwargs["edit"]]
            product_dict = forms.model_to_dict(self.object)
            product_dict[edit] = input
            form = ProductForm(product_dict)
            if form.is_valid():
                new_record = form.save(commit=False)
                exec("self.object." + edit + " = " + "new_record." + edit)
                self.object.save(update_fields=[edit])
                return HttpResponseRedirect(
                    reverse("product_details", kwargs={"pk": kwargs["pk"]})
                )
            else:
                return HttpResponseRedirect(
                    reverse("product_details", kwargs={"pk": kwargs["pk"]})
                )
        else:
            return super().post(self, request, *args, **kwargs)


class EditReviewProductDetailsView(LoginRequiredMixin, ProductDetailsView):
    editable = ("review",)

    def get(self, request, *args, **kwargs):
        # Pass get's 'edit' value to instance variable self.edit. If no variabe.
        try:
            self.edit = kwargs["edit"]
            try:
                self.index = kwargs["index"]  # TODO: change to uuid pk review
            except KeyError:
                self.index = None
        except KeyError:
            self.edit = False

        return super().get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.edit and self.index != None:
            # Change field in product dict, choosen by get's variable self.edit,
            # to form's widget. Pass it to the context.
            if self.edit in self.editable:
                reviews_list = list(self.object.reviews.all())
                # Check if user can edit review
                author = reviews_list[self.index].author
                if not self.is_author_permitted(author):
                    return self.handle_no_permission()
                form = ReviewForm(initial={"review": reviews_list[self.index].review})
                form["review"].field.widget.attrs.update(
                    size=len(reviews_list[self.index].review)
                )
                reviews_list[self.index] = {
                    "review": form["review"],
                    "author": reviews_list[self.index].author,
                }
                context["reviews"] = reviews_list
                context["edit"] = self.edit
                context["index"] = self.index

        return context

    def post(self, request, *args, **kwargs):
        try:
            edit = kwargs["edit"]
        except KeyError:
            edit = False

        if edit:
            if edit in self.editable and "edit-review" in request.POST:
                self.review = Product.objects.get(pk=kwargs["pk"]).reviews.all()[
                    kwargs["index"]
                ]

                input = request.POST["review"]
                rev_dict = forms.model_to_dict(self.review)
                rev_dict["review"] = input
                form = ReviewForm(rev_dict)
                if form.is_valid():
                    new_record = form.save(commit=False)
                    self.review.review = new_record.review
                    self.review.save()
                return HttpResponseRedirect(
                    reverse("product_details", kwargs={"pk": kwargs["pk"]})
                )
            elif "add-review" in request.POST:
                return super().post(request, *args, **kwargs)
        else:
            return super().post(self, request, *args, **kwargs)

    def is_author_permitted(self, author):
        is_author = False
        if (
            self.request.user == author
            or self.request.user.is_superuser
            or self.request.user.is_staff
        ):
            is_author = True
        return is_author


class SearchResultView(TemplateView):
    template_name = "search_result.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        phrase = self.request.GET.get("phrase", None)
        if phrase:
            context["phrase"] = phrase
            search_results = self.search(phrase)
            queryset = Product.objects.filter(
                pk__in={product.pk for product in search_results}
            )
            associated_products_context = ProductListView(
                queryset=queryset.prefetch_related(
                    Prefetch(
                        "images", Image.objects.filter(place=0), to_attr="thumbnail"
                    )
                ),
                kwargs=kwargs,
                request=self.request,
            ).get_context_data()

            merged_context = {**context, **associated_products_context}
        return merged_context

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


# Product
class CheckboxView(ListView):
    """View meant only for inheritance. Allows to make checkbox view to manage
    many to many relationship."""

    # Partner model is model that you assign to.
    partner_model = None
    relation_name = None
    form = CheckboxForm

    def get(self, request, *args, **kwargs):
        self.partner = self.get_partner_model().objects.get(pk=kwargs["pk"])
        self._set_relation_queryset()
        return super().get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        addable_objects = list()
        already_added = list()
        for object in self.object_list:
            if object not in self.relation_queryset:
                addable_objects.append((object.pk, object.name))
            else:
                already_added.append((object.pk, object.name))
        context["partner_object"] = self.partner
        context["form_addable"] = self.form(choices=addable_objects)
        context["form_already_added"] = self.form(choices=already_added)
        return context

    def _set_relation_queryset(self):
        """Set relations queryset that contains every record that is connected to
        partner_model."""
        if self.relation_name is None:
            raise ValueError("You have to specify relation name.")

        self.relation_queryset = eval("self.partner." + self.relation_name + ".all()")

    def get_partner_model(self):
        """Return pratner model"""
        if self.partner_model is None:
            raise ValueError("You have to specify partner model.")
        return self.partner_model

    def post(self, request, *args, **kwargs):
        # You have to provide 'add_button', 'delete_button' in post request in
        # order to get post to work.
        self.partner = self.get_partner_model().objects.get(pk=kwargs["pk"])
        choices = request.POST.getlist("choices")
        queryset = self.model.objects.filter(pk__in=choices)

        if "delete_button" in request.POST:
            for record in queryset:
                self.manage_record(record=record, order="remove")
        elif "add_button" in request.POST:
            for record in queryset:
                self.manage_record(record=record, order="add")

        return render(
            request,
            self.template_name,
            self.get(request, *args, **kwargs).context_data,
        )

    def manage_record(self, record=None, order=None):
        """Dynamically exec allowed operations for many to many relationship."""
        allowed = ("add", "remove")
        if order is None:
            raise ValueError("Order for _manage_record can't be None value.")

        if record is None:
            raise ValueError("Record to manage can't be None value")

        if record.__class__ is not self.model:
            raise ValueError("Record have to be " + str(self.model) + " instance.")

        if order in allowed:
            exec("self.partner." + self.relation_name + "." + order + "(record)")
        else:
            raise Exception("Order " + order + " not allowed.")


class ProductManageCategoriesView(
    LoginRequiredMixin, StaffPrivilegesRequiredMixin, CheckboxView
):
    """Class that provides categories management feture."""

    model = Category
    partner_model = Product
    relation_name = "categories"
    template_name = "category_checkbox.html"


class ProductAssignCategoriesView(ProductManageCategoriesView):
    """Class that allows to assign categories in ProductCreateView"""

    def get_context_data(self, **kwargs):
        context = dict(kwargs)
        addable_objects = list()
        for object in self.object_list:
            addable_objects.append((object.pk, object))
        # TODO change form to model multichocice?
        context["form_addable"] = self.form(choices=addable_objects)
        return context

    def post(self, request, *args, **kwargs):
        self.partner = self.get_partner_model().objects.get(pk=kwargs["pk"])
        choices = request.POST.getlist("choices")
        queryset = self.model.objects.filter(pk__in=choices)
        if "add_product" in request.POST:
            for record in queryset:
                self.manage_record(record=record, order="add")
