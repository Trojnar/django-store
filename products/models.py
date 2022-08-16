from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model
import uuid


class Product(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(max_length=200)
    producer = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("product_details", kwargs={"pk": self.pk})


# TODO: change pk to uuid, add ordering by placee
class Image(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="product_images/", blank=True)
    # Place values tells what position in display order image will have.
    place = models.IntegerField(blank=True)

    def delete(self, using=None, keep_parents=False):
        self.image.storage.delete(self.image.name)
        super().delete()


class Transaction(models.Model):
    date = models.DateField()
    closed = models.BooleanField(default=False)


class Cart(models.Model):
    product = models.ManyToManyField(
        Product,
        related_name="carts",
    )
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="cart",
    )
    transaction = models.ForeignKey(
        Transaction, on_delete=models.CASCADE, blank=True, related_name="products"
    )


class Categorie(models.Model):
    products = models.ManyToManyField(
        Product,
        related_name="categories",
    )
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("categorie_details", kwargs={"pk": self.pk})
