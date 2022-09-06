from django.contrib import admin
from .models import CartItem, Cart


class CartItemInline(admin.TabularInline):
    model = CartItem


class CartAdmin(admin.ModelAdmin):
    inlines = [
        CartItemInline,
    ]
    list_display = ("user", "transaction")
    fields = ("user",)


admin.site.register(
    Cart,
    CartAdmin,
)
