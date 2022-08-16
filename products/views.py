import uuid


import uuid
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
    PermissionRequiredMixin,
    UserPassesTestMixin,
    LoginRequiredMixin,
)
from django import forms
from django.forms import inlineformset_factory

from .models import Product, Image, Categorie
from .forms import (
    ImagesManagerForm,
    ProductForm,
    ProductFormWithImage,
    ImageForm,
    ImagesManagerUploadImageForm,
    CategorieCheckboxForm,
)
from reviews.forms import ReviewForm
from reviews.models import Review
from reviews.views import CreateReviewView, UpdateReviewView


from itertools import chain


class ProductListView(ListView):
    model = Product
    template_name = "product_list.html"


# TODO make it look like CategorieListView or just make custom form
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
        view = CreateReviewView()
        view.request = self.request
        return view.post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["new_review"] = "You can enter your review here. "
        context["reviews"] = self.object.reviews.all()
        context["images"] = ImageManagerView.get_sorted_images(self, self.object)
        return context


class ProductCreateView(PermissionRequiredMixin, CreateView):
    model = Product
    template_name = "product_create.html"
    permission_required = "products.add_product"
    form_class = ProductFormWithImage

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
            return super().form_valid(form)


class ProductUpdateView(UpdateView):
    model = Product
    template_name = "product_create.html"
    from_class = ProductFormWithImage
    fields = ("name", "producer", "price", "image")


class ImagesUpload(FormView):
    form_class = ImagesManagerUploadImageForm
    template_name = "upload_images.html"

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        images = request.FILES.getlist("image")
        if form.is_valid():
            product = Product.objects.get(pk=request.POST["product_pk"])
            images_queryset = product.images.all()
            for index, image in enumerate(images):
                Image.objects.create(
                    product=product,
                    image=image,
                    place=index
                    + len(images_queryset),  # set diplay position at the end of list
                )
        return HttpResponseRedirect(self.success_url)


class ImageDeleteView(DeleteView):
    model = Image
    success_url = reverse_lazy("product_list")


class ImageManagerView(FormView):
    template_name = "images_manager.html"
    form_class = ImagesManagerForm

    def get(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data(**kwargs))

    def get_context_data(self, **kwargs):
        product = Product.objects.get(pk=kwargs["pk"])
        images = self.get_sorted_images(product)

        kwargs["upload_images_form"] = ImagesUpload(
            request=self.request,
            initial={"product_pk": product.pk},
        ).get_context_data()["form"]

        if images:
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
            # TODO use json for manage position
            images = self.get_sorted_images(request.POST["product_pk"])
            image = images.get(pk=request.POST["image_pk"])
            image.place -= 1
            image.place = self.adjust_index_to_range(0, images.count() - 1, image.place)
            if image.place != 0:
                next_image = images.get(place=image.place)
                next_image.place += 1
                next_image.place = self.adjust_index_to_range(
                    0, images.count() - 1, next_image.place
                )
                next_image.save()
            image.save()
        elif "move_down" in request.POST:
            # Changes image display position to lower.
            images = self.get_sorted_images(request.POST["product_pk"])
            image = images.get(pk=request.POST["image_pk"])
            image.place += 1
            image.place = self.adjust_index_to_range(0, images.count() - 1, image.place)
            if image.place != images.count():
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
                success_url=reverse(
                    "images_manager", kwargs={"pk": request.POST["product_pk"]}
                ),
                initial={"product_pk": request.POST["product_pk"]},
            )(self.request)

        return HttpResponseRedirect(
            reverse("images_manager", kwargs={"pk": request.POST["product_pk"]})
        )

    def get_sorted_images(self, product):
        return Image.objects.filter(product=product).order_by("place")

    def adjust_index_to_range(self, start, end, index):
        if index > end:
            index = end
        elif index < start:
            index = 0
        return index


class EditProductDetailsView(
    LoginRequiredMixin, UserPassesTestMixin, ProductDetailsView
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

    def test_func(self):
        authorized = False
        user = self.request.user
        if user.is_staff or user.is_superuser:
            authorized = True
        return authorized


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


class CategorieListView(ListView):
    model = Categorie
    template_name = "categorie_list.html"
    success_url = reverse_lazy("categorie_list")

    def get(self, request, *args, **kwargs):
        self.request = request
        return super().get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "categorie_create" in self.request.POST:
            self.request.method = "GET"
            context["categorie_create_form"] = CategorieCreateView(
                request=self.request
            ).get_form()
        elif "categorie_update" in self.request.POST:
            self.request.method = "GET"
            context["categorie_update_form"] = CategorieUpdateView(
                request=self.request
            ).get_form()
            context["form_pk"] = self.request.POST["categorie_pk"]
            # Set placeholder text for update form
            context["categorie_update_form"] = (
                context["categorie_update_form"]
                .fields["name"]
                .widget.render(
                    "name",
                    context["object_list"]
                    .get(pk=self.request.POST["categorie_pk"])
                    .name,
                )
            )
        return context

    def post(self, request, *args, **kwargs):
        if "submit_categorie_create" in self.request.POST:
            CategorieCreateView.as_view()(request)
        elif "categorie_delete" in self.request.POST:
            CategorieDeleteView.as_view()(request, pk=self.request.POST["categorie_pk"])
        elif "submit_categorie_update" in self.request.POST:
            CategorieUpdateView.as_view()(request, pk=self.request.POST["categorie_pk"])
        return render(
            request,
            "categorie_list.html",
            self.get(request, *args, **kwargs).context_data,
        )


class CategorieCreateView(CreateView):
    model = Categorie
    template_name = "categorie_create.html"
    fields = ("name",)


class CategorieDeleteView(DeleteView):
    model = Categorie
    success_url = reverse_lazy("categorie_list")


class CategorieUpdateView(UpdateView):
    model = Categorie
    template_name = "categorie_update.html"
    fields = ("name",)

    def post(self, request, *args, **kwargs):
        self.request = request
        return super().post(request, *args, **kwargs)


class CategorieDetailsView(DetailView):
    model = Categorie
    template_name = "categorie_details.html"


class CategorieCheckboxView(ListView):
    model = Product
    template_name = "categorie_checkbox.html"

    def get(self, request, *args, **kwargs):
        self.categorie = Categorie.objects.get(pk=kwargs["pk"])
        return super().get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        addable_products = list()
        already_added = list()
        for product in self.object_list:
            if product not in self.categorie.products.all():
                addable_products.append((product.pk, product))
            else:
                already_added.append((product.pk, product))
        context["categorie"] = self.categorie
        context["form_addable"] = CategorieCheckboxForm(choices=addable_products)
        context["form_already_added"] = CategorieCheckboxForm(choices=already_added)
        return context

    def post(self, request, *args, **kwargs):
        categorie = Categorie.objects.get(pk=request.POST["categorie_pk"])
        choices = request.POST.getlist("choices")
        products_queryset = Product.objects.filter(pk__in=choices)
        if "delete_button" in request.POST:
            for product in products_queryset:
                categorie.products.remove(product)
        elif "add_button" in request.POST:
            for product in products_queryset:
                categorie.products.add(product)

        return render(
            request,
            "categorie_checkbox.html",
            self.get(request, *args, **kwargs).context_data,
        )
