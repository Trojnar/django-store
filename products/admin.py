from django.contrib import admin
from .models import Product, Image, Categorie, CartItem, Cart
from reviews.models import Review


class ReviewInline(admin.TabularInline):
    model = Review


class ImageInline(admin.TabularInline):
    model = Image


class CategorieInline(admin.TabularInline):
    model = Categorie.products.through


class CartItemInline(admin.TabularInline):
    model = CartItem


class CartAdmin(admin.ModelAdmin):
    inlines = [
        CartItemInline,
    ]
    list_display = ("user", "transaction")
    fields = ("user",)


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
admin.site.register(
    Cart,
    CartAdmin,
)
