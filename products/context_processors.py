from asyncio.windows_events import NULL
from django.contrib.auth import get_user_model


def cart(request):
    return {
        "carts": None  # request.user.carts.prefetch_related("transaction")
        # .filter(
        #     transaction=None
        # )
    }
    # queryset = Product.objects.prefetch_related(
    #     Prefetch("reviews", Review.objects.select_related("author"))
    # )
