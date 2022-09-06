from django.db import models
from django.urls import reverse
from products.models import Product


class Category(models.Model):
    products = models.ManyToManyField(
        Product,
        related_name="categories",
    )
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("category_details", kwargs={"pk": self.pk})

    class Meta:
        verbose_name_plural = "categories"
