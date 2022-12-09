from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    FormView,
    DeleteView,
)

from .models import Image
from products.models import Product
from .forms import (
    ImagesManagerForm,
    ImagesManagerUploadImageForm,
)
from accounts.utils.utils import StaffPrivilegesRequiredMixin


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
            # Initialization of the first form happened in super().get_context_data
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
