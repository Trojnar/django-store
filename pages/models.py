from django.db import models
from products.models import Product


class HomepageCategory(models.Model):
    """
    Category that's exclusive to homepage. It's made with categories such as
    promotions, bestsellers etc. in mind.
    """

    products = models.ManyToManyField(
        Product,
        related_name="homepage_categories",
    )
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name

    # TODO:
    # def get_absolute_url(self):
    #     return reverse("homepage_category_details", kwargs={"pk": self.pk})

    class Meta:
        verbose_name_plural = "homepage_categories"
