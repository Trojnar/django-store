from django.db import models
from django.urls import reverse
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    def get_absolute_url(self):
        return reverse("users_detail", kwargs={"pk": self.pk})
