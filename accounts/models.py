from django.db import models
from django.urls import reverse
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model


class CustomUser(AbstractUser):
    def get_absolute_url(self):
        return reverse("users_detail", kwargs={"pk": self.pk})


class Address(models.Model):
    # TODO move to accounts app
    address = models.CharField(max_length=128)
    city = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=10)

    # For logged in user
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        related_name="addresses",
    )

    def get_absolute_url(self):
        return reverse("address_manage")
