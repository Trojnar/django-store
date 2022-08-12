from django.contrib import admin
from .models import Product, Image
from reviews.models import Review


class ReviewInline(admin.TabularInline):
    model = Review


class ImageInline(admin.TabularInline):
    model = Image


class ProductAdmin(admin.ModelAdmin):
    inlines = [
        ReviewInline,
        ImageInline,
    ]
    list_display = (
        "name",
        "producer",
        "price",
    )


admin.site.register(Product, ProductAdmin)
