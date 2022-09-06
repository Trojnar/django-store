from django.contrib import admin
from .models import Product
from reviews.models import Review
from categories.admin import CategoryInline
from images.admin import ImageInline


class ReviewInline(admin.TabularInline):
    model = Review


class ProductAdmin(admin.ModelAdmin):
    inlines = [
        ReviewInline,
        ImageInline,
        CategoryInline,
    ]
    list_display = (
        "name",
        "producer",
        "price",
    )
    exclude = ("product",)


admin.site.register(
    Product,
    ProductAdmin,
)
