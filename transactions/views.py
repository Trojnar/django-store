from datetime import datetime
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.views.generic import (
    ListView,
    TemplateView,
    UpdateView,
)
from django.db.models import Prefetch
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
)

from accounts.views import AddressCreate
from accounts.forms import CustomUserNameForm
from .models import Cart, CartItem, Transaction
from products.models import Product
from .forms import (
    CartItemForm,
    RadioForm,
)
from accounts.utils.utils import StaffPrivilegesRequiredMixin


class ObjectOwnershipRequiredMixin:
    """Raise page not found exception if object in UpdateView or DeleteView is not
    request's user property"""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.__is_object_property = False

    def get_object(self, queryset=None):
        """Raise page not found exception if object is not request's user property"""
        object = super().get_object(queryset=queryset)
        self.__is_object_property = self._is_object_users_property(object)
        if not self.__is_object_property:
            raise Http404()
        return object

    def _is_object_users_property(self, object):
        """Tests if it's user's cart, if not returns forbidden response."""
        if self.request.user.pk != object.user.pk:
            return False

        return True


class CartView(LoginRequiredMixin, ObjectOwnershipRequiredMixin, UpdateView):
    """
    Cart view for get and post form for Cart model. Template context cart data is
    fetched from db through context processor 'cart', so only forms are added to the
    context.
    """

    template_name = "transactions/cart_details.html"
    form_class = CartItemForm
    model = Cart

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        kwargs["forms"] = self.get_forms()

        return self.render_to_response(self.get_context_data(**kwargs))

    def get_forms(self, object=None):
        if object is None:
            if self.object is None:
                raise ValueError("object can't be None value.s")
            object = self.object

        forms = list()
        for cart_item in object.cart_items.all():
            # set initial for each cart item form
            self.initial = {"count": cart_item.count}
            form = self.get_form()
            forms.append(form)
        return forms

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        assert (
            self.object.transaction is None
        ), "Cart can't have assigned transaction in order to edit"
        cart_pk = kwargs.get("pk")

        # TODO message errors
        errors = list()

        if "delete_button" in request.POST:
            # delete cart item
            cart_item = self.object.cart_items.get(pk=request.POST["cart_item_pk"])
            self.cart_item_delete(cart_item)
        elif "cart_add_button" in request.POST:
            # button placed in other templates
            product = Product.objects.get(pk=kwargs["product_pk"])
            if product.pk in self.object.cart_items.values_list("product", flat=True):
                cart_item = self.object.cart_items.get(product=product)
                self.cart_item_update(cart_item, cart_item.count + 1)
            else:
                cart_item = CartItem.objects.create(product=product, cart=self.object)
                self.cart_item_update(cart_item, cart_item.count + 1)
        elif "save_button" in request.POST or "buy_button" in request.POST:
            # set new item count if changed
            counts = list(map(int, request.POST.getlist("count")))
            cart_item_pks = request.POST.getlist("cart_item_pk")
            queryset = self.object.cart_items.filter(pk__in=cart_item_pks)
            for pk, count in zip(cart_item_pks, counts):
                cart_item = queryset.get(pk=pk)
                self.cart_item_update(cart_item, count)

            if "buy_button" in request.POST:
                # redirect to transaction view
                return HttpResponseRedirect(
                    reverse("transaction", kwargs={"pk": cart_pk})
                )

        return HttpResponseRedirect(reverse("cart_details", kwargs={"pk": cart_pk}))

    def cart_item_delete(self, cart_item):
        """Delete cart item."""
        cart_item.product.count += cart_item.count
        cart_item.product.save()
        cart_item.delete()

    def cart_item_update(self, cart_item, update_value):
        """Update cart item by update_value value."""
        difference = update_value - cart_item.count
        # TODO message errors
        errors = []
        if update_value == 0:
            self.cart_item_delete(cart_item)
        elif difference > 0:
            if cart_item.product.count >= difference:
                cart_item.count = update_value
                cart_item.product.count -= difference
                cart_item.save()
                cart_item.product.save()
            else:
                errors.append(f"Only {cart_item.product.count} left.")
        elif difference < 0:
            cart_item.count = update_value
            cart_item.product.count -= difference
            cart_item.save()
            cart_item.product.save()
        elif difference == 0:
            pass
        else:
            # no change
            pass

        return errors

    def cart_count_price(self, cart=None):
        """Count cart price"""
        if cart is None:
            cart = self.object

        price = 0
        for cart_item in cart.cart_items.all():
            price += cart_item.product.price * cart_item.count
        cart.price = price
        cart.save()


class TransactionView(TemplateView):
    template_name = "transactions/transaction.html"
    shipping_methods = (
        "UPS",
        "DPD",
    )
    payment_methods = (
        "cash on delivery",
        "payment_2",
    )

    def get(self, request, add_new_address_form_errors={}, *args, **kwargs):
        # name, last_name
        kwargs["name_form"] = CustomUserNameForm(
            first_name=request.user.first_name,
            last_name=request.user.last_name,
            required=True,
        )

        # addresses
        addresses = request.user.addresses.all()
        choices = list()
        for address in addresses:
            label = f"{address.address}\n {address.city}\n {address.postal_code}\n"
            choices.append((address.pk, label))
        choices.append(("new", "New address:"))
        kwargs["choose_address_form"] = RadioForm(
            choices=choices, name="radio_address", required=True
        )
        kwargs["add_new_address_form"] = AddressCreate(
            request=request
        ).get_form_class()(initial={"user": request.user}, required=False)
        # form validation errors for address form
        kwargs["add_new_address_form"].errors.update(add_new_address_form_errors)

        # shipping methods
        shipping_methods_choices = list()
        for shipping_method in self.shipping_methods:
            shipping_methods_choices.append((shipping_method, shipping_method))
        kwargs["shipping_methods_form"] = RadioForm(
            choices=shipping_methods_choices, name="radio_shipping", required=True
        )

        # payment methods
        payment_methods_choices = list()
        for payment_method in self.payment_methods:
            payment_methods_choices.append((payment_method, payment_method))
        kwargs["payment_methods_form"] = RadioForm(
            choices=payment_methods_choices, name="radio_payment", required=True
        )

        return super().get(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if "proceed_to_payment_button" in request.POST:

            # addresses
            if "radio_address" in request.POST:
                if request.POST["radio_address"] == "new":
                    response = AddressCreate.as_view()(request)
                    if (
                        response.status_code == 200
                        and not response.context_data["form"].is_valid()
                    ):
                        # If form validation errors
                        kwargs["add_new_address_form_errors"] = response.context_data[
                            "form"
                        ].errors
                        request.method = "GET"
                        return self.get(request, **kwargs)
                    else:
                        # If form valid, get created address.
                        address = request.user.addresses.last()
                else:
                    address = request.user.addresses.get(
                        pk=request.POST["radio_address"]
                    )
            else:
                raise Exception("radio_address value have to be in post request.")

            # frist_name, last_name
            if "first_name" in request.POST and "last_name" in request.POST:
                if request.user.is_authenticated:
                    request.user.first_name = request.POST["first_name"]
                    request.user.last_name = request.POST["last_name"]
                    request.user.save()
                else:
                    # TODO Guest transaction
                    pass
            else:
                raise Exception(
                    "first_name and last_name value have to be in post request."
                )

            # shipping method
            if "radio_shipping" in request.POST:
                shipping = request.POST["radio_shipping"]
            else:
                raise Exception("Post request has no value 'radio_shipping'")

            # payment method
            if "radio_payment" in request.POST:
                payment_method = request.POST["radio_payment"]
            else:
                raise Exception("Post request has no value 'radio_payment'")

            # Create transaction
            if request.user.is_authenticated:
                # Get shopping cart
                cart = request.user.carts.get(transaction=None)
                # Create and add transaction to cart
                cart.transaction = Transaction.objects.create(
                    date=datetime.now(),
                    status="",
                    tracking_number="",
                    address=address,
                    shipping_method=shipping,
                )
                cart.save()
            else:
                # TODO Guest transaction
                pass

            # payment method redirection
            match payment_method:
                case "cash on delivery":
                    cart.transaction.payment_method = payment_method
                    cart.transaction.status = "pending for shipping"
                    cart.transaction.save()
                    return HttpResponseRedirect(reverse("home"))
                case other:
                    kwargs[
                        "payment_error"
                    ] = f"Method {other} is not supported right now."


class TransactionsUserListView(ListView):
    """View of history of transactions"""

    ordering = "transaction__date"
    queryset = None
    template_name = "transactions/transaction_history.html"

    def get_queryset(self):
        self.queryset = (
            self.request.user.carts.exclude(transaction=None)
            .select_related("transaction__address")
            .prefetch_related(
                Prefetch("cart_items", CartItem.objects.select_related("product"))
            )
        )
        return super().get_queryset()


class TransactionStaffListView(StaffPrivilegesRequiredMixin, ListView):
    """View for managing transactions"""

    pass
