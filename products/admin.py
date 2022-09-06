from django.contrib import admin
from .models import Product, Image
from reviews.models import Review
from categories.admin import CategoryInline


class ReviewInline(admin.TabularInline):
    model = Review


class ImageInline(admin.TabularInline):
    model = Image


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
