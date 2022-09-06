from django.db.models import Prefetch
from django.core.exceptions import MultipleObjectsReturned
from .models import CartItem, Cart
from .views import CartView


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

    CartView().cart_count_price(cart=cart)

    forms = CartView(
        object=cart,
        request=request,
    ).get_forms()

    return {
        "cart_object": cart,
        "cart_cart_items_len": len(cart.cart_items.all()),
        "forms": forms,
    }
