from django.db import models
from products.models import Product
from django.contrib.auth import get_user_model


class Review(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    review = models.CharField(max_length=255)
    author = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="reviews",
    )

    def __str__(self):
        if len(self.review) > 20:
            return self.review[:20] + "..."
        else:
            return self.review
