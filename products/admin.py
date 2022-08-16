from django.contrib import admin
from .models import Product, Image, Categorie
from reviews.models import Review


class ReviewInline(admin.TabularInline):
    model = Review


class ImageInline(admin.TabularInline):
    model = Image


class CategorieInline(admin.TabularInline):
    model = Categorie.products.through


class CategorieAdmin(admin.ModelAdmin):
    inline = [
        CategorieInline,
    ]
    exclude = ("categorie",)
    list_display = ("name",)


class ProductAdmin(admin.ModelAdmin):
    inlines = [
        ReviewInline,
        ImageInline,
        CategorieInline,
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
admin.site.register(
    Categorie,
    CategorieAdmin,
)
