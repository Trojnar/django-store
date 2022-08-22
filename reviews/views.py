from django.views.generic import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.urls import reverse
from products.models import Product
from .models import Review
from .forms import ReviewForm


class CreateReviewView(LoginRequiredMixin, CreateView):
    model = Review
    template_name = "review_create.html"
    form_class = ReviewForm

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        if self.request.user.is_authenticated:
            if form.is_valid():
                self.object = form.save(commit=False)
                self.object.product = Product.objects.get(pk=kwargs["pk"])
                self.object.author = self.request.user
                self.object.save()
                self.success_url = reverse_lazy(
                    "product_details", kwargs={"pk": self.object.product.pk}
                )
                return HttpResponseRedirect(self.get_success_url())
            else:
                return self.render_to_response(self.get_context_data(form=form))
        else:
            # TODO: redirect and input after login
            # https://stackoverflow.com/questions/42389168/django-login-user-af
            # ter-successful-login-user-stay-on-same-page
            return HttpResponseRedirect(reverse("account_login"))


class CreateReviewView(LoginRequiredMixin, CreateView):
    model = Review
    template_name = "review_create.html"
    form_class = ReviewForm

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        if self.request.user.is_authenticated:
            if form.is_valid():
                self.object = form.save(commit=False)
                self.object.product = Product.objects.get(pk=kwargs["pk"])
                self.object.author = self.request.user
                self.object.save()
                self.success_url = reverse_lazy(
                    "product_details", kwargs={"pk": self.object.product.pk}
                )
                return HttpResponseRedirect(self.get_success_url())
            else:
                return self.render_to_response(self.get_context_data(form=form))
        else:
            # TODO: redirect and input after login
            # https://stackoverflow.com/questions/42389168/django-login-user-af
            # ter-successful-login-user-stay-on-same-page
            return HttpResponseRedirect(reverse("account_login"))


class UpdateReviewView(UpdateView):
    model = Review
    template_name = "review_create.html"
    form_class = ReviewForm

    def get_success_url(self) -> str:
        return reverse_lazy("product_details", kwargs={"pk": self.object.product.pk})

    def _post(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs
        return super().post(self, self.request, *self.args, **self.kwargs)
