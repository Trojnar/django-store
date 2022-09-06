from django.db import models
from django.contrib.auth import get_user_model

from products.models import Product
from accounts.models import Address


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
