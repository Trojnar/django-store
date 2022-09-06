from django.db import models
from products.models import get_product_model

# TODO: change pk to uuid, add ordering by placee
class Image(models.Model):
    product = models.ForeignKey(
        get_product_model(),
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="product_images/", blank=True)
    # Place values tells what position in display order image will have.
    place = models.IntegerField(blank=True)

    def delete(self, using=None, keep_parents=False):
        self.image.storage.delete(self.image.name)
        super().delete()
