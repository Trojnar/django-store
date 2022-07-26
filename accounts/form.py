from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser


def CustomUserCreationForm(UserCrationForm):
    model = CustomUser
