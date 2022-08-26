from django.db.models import Prefetch
from django.core.exceptions import MultipleObjectsReturned
from .models import CartItem, Cart


def cart(request):
    # TODO change related name 'products', because it's misleading
    if not request.user.is_authenticated:
        return {}

    try:
        cart = (
            request.user.carts.all()
            .prefetch_related(
                Prefetch("cart_items", CartItem.objects.select_related("product"))
            )
            .get(transaction=None)
        )
    except MultipleObjectsReturned:
        raise Exception(
            (
                "There is more carts than expected. One or more cart objects of"
                f" {request.user} user haven't transaction object assigned. Only"
                " one cart object should've blank transaction field."
            )
        )
    except Cart.DoesNotExist:
        # Add blank shopping cart to the user is not exists
        cart = request.user.carts.create()

    return {
        "cart_pk": cart.pk,
        "cart_cart_items": cart.cart_items.all(),
        "cart_cart_items_len": len(cart.cart_items.all()),
    }
