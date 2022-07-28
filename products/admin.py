from django.contrib import admin
from .models import Product
from reviews.models import Review


class ReviewInline(admin.TabularInline):
    model = Review


class ProductAdmin(admin.ModelAdmin):
    inlines = [
        ReviewInline,
    ]
    list_display = (
        "name",
        "producer",
        "price",
    )


admin.site.register(Product, ProductAdmin)
