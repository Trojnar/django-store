from django.views.generic.edit import CreateView
from django.views.generic import TemplateView
from .models import CustomUser
from .forms import CustomUserCreationForm
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    model = CustomUser
    template_name = "registration/signup.html"
    success_url = reverse_lazy("home")


class AccountSettingsView(LoginRequiredMixin, TemplateView):
    template_name = "account/settings.html"
