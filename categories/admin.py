from django.contrib import admin
from .models import Category


class CategoryInline(admin.TabularInline):
    model = Category.products.through


class CategoryAdmin(admin.ModelAdmin):
    inline = [
        CategoryInline,
    ]
    exclude = ("category",)
    list_display = ("name",)


admin.site.register(
    Category,
    CategoryAdmin,
)
