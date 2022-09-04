from datetime import datetime
from django.http import HttpResponseRedirect, HttpResponseForbidden, Http404
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.shortcuts import render
from django.contrib.auth import get_user_model
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
from django.contrib.auth.decorators import login_required
from django import forms

from accounts.views import AddressCreate
from accounts.forms import CustomUserNameForm
from .models import Cart, Product, Image, Category, CartItem, Transaction
from .forms import (
    ImagesManagerForm,
    ProductForm,
    ProductFormWithImage,
    ImageForm,
    ImagesManagerUploadImageForm,
    CheckboxForm,
    CartItemForm,
    RadioForm,
)
from reviews.forms import ReviewForm
from reviews.models import Review
from reviews.views import CreateReviewView
from accounts.views import StaffPrivilegesRequiredMixin


from itertools import chain


class ProductListView(ListView):
    model = Product
    template_name = "product_list.html"
    ordering = "name"
    rows_count = 4

    def get_context_data(self, **kwargs):
        """split product to rows to display them on page"""
        product_rows = list()
        row = list()
        for index, object in enumerate(self.object_list):
            row.append(object)
            if ((index + 1) % self.rows_count) == 0:
                product_rows.append(row)
                row = list()

        # Add blank items to row to make last row the same length
        for index in range(
            self.rows_count - (self.object_list.count() % self.rows_count)
        ):
            row.append("blank")
        product_rows.append(row)

        kwargs["product_rows"] = product_rows
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            self.cart_add_button(request)
        return HttpResponseRedirect(reverse("product_list"))

    def cart_add_button(self, request):
        if "cart_add_button" in request.POST:
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


class ImageManagerView(StaffPrivilegesRequiredMixin, FormView):
    """View that provides managing images feature for product."""

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
        # use ProductListView get_context_data method to split category products to rows
        context = super().get_context_data(**kwargs)
        product_list_context = ProductListView(
            object_list=self.object.products.all()
        ).get_context_data()
        context["product_rows"] = product_list_context["product_rows"]
        return context

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


class CategoryManageProductsView(
    LoginRequiredMixin, StaffPrivilegesRequiredMixin, CheckboxView
):
    model = Product
    partner_model = Category
    relation_name = "products"
    template_name = "category_checkbox.html"


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


class ObjectOwnershipRequiredMixin:
    """Raise page not found exception if object in UpdateView or DeleteView is not
    request's user property"""

    def __init__(self):
        self.__is_object_property = False

    def get_object(self, queryset=None):
        """Raise page not found exception if object is not request's user property"""
        object = super().get_object(queryset=queryset)
        self.__is_object_property = self._is_object_users_property(object)
        if not self.__is_object_property:
            raise Http404()
        return object

    def _is_object_users_property(self, object):
        """Tests if it's user's cart, if not returns forbidden response."""
        if self.request.user.pk != object.user.pk:
            return False

        return True


class CartView(LoginRequiredMixin, ObjectOwnershipRequiredMixin, UpdateView):
    """
    Cart view for get and post form for Cart model. Template context cart data is
    fetched from db through context processor 'cart', so only forms are added to the
    context.
    """

    template_name = "cart_details.html"
    form_class = CartItemForm
    model = Cart

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        forms = list()
        for cart_item in self.object.cart_items.all():
            # set initial for each cart item form
            self.initial = {"count": cart_item.count}
            form = self.get_form()
            forms.append(form)
        kwargs["forms"] = forms

        return self.render_to_response(self.get_context_data(**kwargs))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        assert (
            self.object.transaction is None
        ), "Cart can't have assigned transaction in order to edit"
        cart_pk = kwargs.get("pk")

        # TODO message errors
        errors = list()

        if "delete_button" in request.POST:
            # delete cart item
            cart_item = self.object.cart_items.get(pk=request.POST["cart_item_pk"])
            self.cart_item_delete(cart_item)
        elif "cart_add_button" in request.POST:
            # button placed in other templates
            product = Product.objects.get(pk=kwargs["product_pk"])
            if product.pk in self.object.cart_items.values_list("product", flat=True):
                cart_item = self.object.cart_items.get(product=product)
                self.cart_item_update(cart_item, cart_item.count + 1)
            else:
                cart_item = CartItem.objects.create(product=product, cart=self.object)
                self.cart_item_update(cart_item, cart_item.count + 1)
        elif "save_button" in request.POST or "buy_button" in request.POST:
            # set new item count if changed
            counts = list(map(int, request.POST.getlist("count")))
            cart_item_pks = request.POST.getlist("cart_item_pk")
            queryset = self.object.cart_items.filter(pk__in=cart_item_pks)
            for pk, count in zip(cart_item_pks, counts):
                cart_item = queryset.get(pk=pk)
                self.cart_item_update(cart_item, count)

            if "buy_button" in request.POST:
                # redirect to transaction view
                return HttpResponseRedirect(
                    reverse("transaction", kwargs={"pk": cart_pk})
                )

        return HttpResponseRedirect(reverse("cart_details", kwargs={"pk": cart_pk}))

    def cart_item_delete(self, cart_item):
        """Delete cart item."""
        cart_item.product.count += cart_item.count
        cart_item.product.save()
        cart_item.delete()

    def cart_item_update(self, cart_item, update_value):
        """Update cart item by update_value value."""
        difference = update_value - cart_item.count
        # TODO message errors
        errors = []
        if update_value == 0:
            self.cart_item_delete(cart_item)
        elif difference > 0:
            if cart_item.product.count >= difference:
                cart_item.count = update_value
                cart_item.product.count -= difference
                cart_item.save()
                cart_item.product.save()
            else:
                errors.append(f"Only {cart_item.product.count} left.")
        elif difference < 0:
            cart_item.count = update_value
            cart_item.product.count -= difference
            cart_item.save()
            cart_item.product.save()
        elif difference == 0:
            pass
        else:
            # no change
            pass

        return errors

    def cart_count_price(self, cart=None):
        """Count cart price"""
        if cart is None:
            cart = self.object

        price = 0
        for cart_item in cart.cart_items.all():
            price += cart_item.product.price * cart_item.count
        cart.price = price
        cart.save()


class TransactionView(TemplateView):
    template_name = "transaction.html"
    shipping_methods = (
        "UPS",
        "DPD",
    )
    payment_methods = (
        "cash on delivery",
        "payment_2",
    )

    def get(self, request, add_new_address_form_errors={}, *args, **kwargs):
        # name, last_name
        kwargs["name_form"] = CustomUserNameForm(
            first_name=request.user.first_name,
            last_name=request.user.last_name,
            required=True,
        )

        # addresses
        addresses = request.user.addresses.all()
        choices = list()
        for address in addresses:
            label = f"{address.address}\n {address.city}\n {address.postal_code}\n"
            choices.append((address.pk, label))
        choices.append(("new", "New address:"))
        kwargs["choose_address_form"] = RadioForm(
            choices=choices, name="radio_address", required=True
        )
        kwargs["add_new_address_form"] = AddressCreate(
            request=request
        ).get_form_class()(initial={"user": request.user}, required=False)
        # form validation errors for address form
        kwargs["add_new_address_form"].errors.update(add_new_address_form_errors)

        # shipping methods
        shipping_methods_choices = list()
        for shipping_method in self.shipping_methods:
            shipping_methods_choices.append((shipping_method, shipping_method))
        kwargs["shipping_methods_form"] = RadioForm(
            choices=shipping_methods_choices, name="radio_shipping", required=True
        )

        # payment methods
        payment_methods_choices = list()
        for payment_method in self.payment_methods:
            payment_methods_choices.append((payment_method, payment_method))
        kwargs["payment_methods_form"] = RadioForm(
            choices=payment_methods_choices, name="radio_payment", required=True
        )

        return super().get(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if "proceed_to_payment_button" in request.POST:

            # addresses
            if "radio_address" in request.POST:
                if request.POST["radio_address"] == "new":
                    response = AddressCreate.as_view()(request)
                    if (
                        response.status_code == 200
                        and not response.context_data["form"].is_valid()
                    ):
                        # If form validation errors
                        kwargs["add_new_address_form_errors"] = response.context_data[
                            "form"
                        ].errors
                        request.method = "GET"
                        return self.get(request, **kwargs)
                    else:
                        # If form valid, get created address.
                        address = request.user.addresses.last()
                else:
                    address = request.user.addresses.get(
                        pk=request.POST["radio_address"]
                    )
            else:
                raise Exception("radio_address value have to be in post request.")

            # frist_name, last_name
            if "first_name" in request.POST and "last_name" in request.POST:
                if request.user.is_authenticated:
                    request.user.first_name = request.POST["first_name"]
                    request.user.last_name = request.POST["last_name"]
                    request.user.save()
                else:
                    # TODO Guest transaction
                    pass
            else:
                raise Exception(
                    "first_name and last_name value have to be in post request."
                )

            # shipping method
            if "radio_shipping" in request.POST:
                shipping = request.POST["radio_shipping"]
            else:
                raise Exception("Post request has no value 'radio_shipping'")

            # payment method
            if "radio_payment" in request.POST:
                payment_method = request.POST["radio_payment"]
            else:
                raise Exception("Post request has no value 'radio_payment'")

            # Create transaction
            if request.user.is_authenticated:
                # Get shopping cart
                cart = request.user.carts.get(transaction=None)
                # Create and add transaction to cart
                cart.transaction = Transaction.objects.create(
                    date=datetime.now(),
                    status="",
                    tracking_number="",
                    address=address,
                    shipping_method=shipping,
                )
                cart.save()
            else:
                # TODO Guest transaction
                pass

            # payment method redirection
            match payment_method:
                case "cash on delivery":
                    cart.transaction.payment_method = payment_method
                    cart.transaction.status = "pending for shipping"
                    cart.transaction.save()
                    return HttpResponseRedirect(reverse("home"))
                case other:
                    kwargs[
                        "payment_error"
                    ] = f"Method {other} is not supported right now."


class TransactionsUserListView(ListView):
    """View of history of transactions"""

    ordering = "transaction__date"
    queryset = None
    template_name = "transaction_history.html"

    def get_queryset(self):
        self.queryset = (
            self.request.user.carts.exclude(transaction=None)
            .select_related("transaction__address")
            .prefetch_related(
                Prefetch("cart_items", CartItem.objects.select_related("product"))
            )
        )
        return super().get_queryset()


class TransactionStaffListView(StaffPrivilegesRequiredMixin, ListView):
    """View for managing transactions"""

    pass
