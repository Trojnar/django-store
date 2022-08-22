from django.db.models import Prefetch
from .models import CartItem


def cart(request):
    # TODO change related name 'products', because it's misleading
    if not request.user.is_authenticated:
        return {}

    cart = (
        request.user.carts.all()
        .prefetch_related(
            Prefetch("cart_items", CartItem.objects.select_related("product"))
        )
        .get(transaction=None)
    )

    return {
        "cart_pk": cart.pk,
        "cart_cart_items": cart.cart_items.all(),
        "cart_cart_items_len": len(cart.cart_items.all()),
    }
