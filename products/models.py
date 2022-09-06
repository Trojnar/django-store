from django.db import models
from django.urls import reverse
import uuid


class Product(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(max_length=200)
    producer = models.CharField(max_length=200)
    description = models.CharField(max_length=3000)
    price = models.IntegerField()  # price in lowest change of currency
    count = models.IntegerField()  # products in stock

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("product_details", kwargs={"pk": self.pk})


def get_product_model():
    return Product
