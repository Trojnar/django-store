from django.http import HttpResponseRedirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import TemplateView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model


from .models import CustomUser, Address
from .forms import AddressForm, CustomUserCreationForm, CustomUserNameForm


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    model = get_user_model()
    template_name = "registration/signup.html"
    success_url = reverse_lazy("home")


class UserFirstLastNameUpdateView(UpdateView):
    """View that allows to update first and last name for user."""

    model = get_user_model()
    form_class = CustomUserNameForm


class AccountSettingsView(LoginRequiredMixin, TemplateView):
    template_name = "account/settings.html"


class AddressCreate(LoginRequiredMixin, CreateView):
    model = Address
    form_class = AddressForm


class AddressUpdate(LoginRequiredMixin, UpdateView):
    model = Address


class AddressDelete(LoginRequiredMixin, DeleteView):
    model = Address
    success_url = reverse_lazy("address_manage")


class AddressManage(LoginRequiredMixin, TemplateView):
    """Address management based on allauth email template"""

    template_name = "account/address_manage.html"

    def get(self, request, *args, **kwargs):
        initial = {"user": request.user}
        kwargs["form"] = AddressCreate(request=request, initial=initial).get_form()
        return super().get(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if "add_button" in request.POST:
            AddressCreate.as_view()(request)
        if "remove_button" in request.POST:
            AddressDelete.as_view()(request, pk=request.POST["address"])
        return HttpResponseRedirect(reverse("address_manage"))
