from django.contrib import admin
from .models import Product, Image, Category
from reviews.models import Review


class ReviewInline(admin.TabularInline):
    model = Review


class ImageInline(admin.TabularInline):
    model = Image


class CategoryInline(admin.TabularInline):
    model = Category.products.through


class CategoryAdmin(admin.ModelAdmin):
    inline = [
        CategoryInline,
    ]
    exclude = ("category",)
    list_display = ("name",)


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
admin.site.register(
    Category,
    CategoryAdmin,
)
