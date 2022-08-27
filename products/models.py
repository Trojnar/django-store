from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model
import uuid

from accounts.models import Address


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
    # Possible status: pending for payment, pending for shipping, send,
    status = models.CharField(max_length=64)
    tracking_number = models.CharField(max_length=128, blank=True)
    address = models.ForeignKey(
        Address,
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    shipping_method = models.CharField(max_length=128, blank=True)
    payment_method = models.CharField(max_length=128, blank=True)

    # For not logged in users:
    email = models.EmailField(
        blank=True,
    )
    name = models.CharField(max_length=24, blank=True)
    surname = models.CharField(max_length=24, blank=True)


class Cart(models.Model):
    # TODO Blank user only when transaction made, rest of the data filled from cookie
    # then.
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="carts",
        null=True,
    )
    price = models.IntegerField(null=True)  # price of whole cart

    # If transaction not null, new cart is assigned to user.
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.CASCADE,
        null=True,
        related_name="cart",
    )


class CartItem(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="in_cart",
    )
    count = models.IntegerField(
        default=0,
    )
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="cart_items",
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
