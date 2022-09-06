from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from products.models import Product
from .views import TransactionView, CartView, TransactionsUserListView
from .models import Transaction


class CartViewTest(TestCase):
    def setUp(self):
        self.casual_user = get_user_model().objects.create(
            username="testuser",
        )
        self.casual_user.set_password("testpass123")
        self.casual_user.carts.create(transaction=None, price=None)
        self.casual_user.save()

        self.other_user = get_user_model().objects.create(
            username="otheruser",
        )
        self.other_user.set_password("testpass123")
        self.other_user.carts.create(transaction=None, price=None)
        self.other_user.save()

        self.product1 = Product.objects.create(
            name="product_name1",
            producer="test_producer",
            price=100,
            count=1000,
        )
        self.product2 = Product.objects.create(
            name="product_name2",
            producer="test_producer2",
            price=200,
            count=1000,
        )
        self.product3 = Product.objects.create(
            name="product_name3",
            producer="test_producer3",
            price=300,
            count=11234,
        )

        self.cart = self.casual_user.carts.get(transaction=None)
        self.cart_item1 = self.cart.cart_items.create(product=self.product1, count=1)
        self.cart_item2 = self.cart.cart_items.create(product=self.product2, count=2)
        self.cart_item3 = self.cart.cart_items.create(product=self.product3, count=5)
        # self.cart.cart_items.add(self.cart_item1)
        # self.cart.cart_items.add(self.cart_item2)
        # self.cart.cart_items.add(self.cart_item3)

        assert self.client.login(username="testuser", password="testpass123")
        self.response = self.client.get(
            reverse("cart_details", kwargs={"pk": self.cart.pk})
        )

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_used_template(self):
        self.assertEqual(*self.response.template_name, "transactions/cart_details.html")

    def test_used_view(self):
        self.assertEqual(
            type(self.response.context["view"]).__name__,
            CartView.__name__,
        )

    def test_products_in_cart(self):
        self.assertContains(self.response, self.cart_item1.product.name)
        self.assertContains(self.response, self.cart_item2.product.name)
        self.assertContains(self.response, self.cart_item3.product.name)
        self.assertContains(self.response, self.cart_item1.count)
        self.assertContains(self.response, self.cart_item2.count)
        self.assertContains(self.response, self.cart_item3.count)

    def test_form_in_context(self):
        self.assertIn("form", self.response.context_data)

    def test_delete_product_from_cart(self):
        response = self.client.post(
            reverse("cart_details", kwargs={"pk": self.cart.pk}),
            data={
                "cart_item_pk": self.cart_item1.pk,
                "delete_button": "delete",
            },
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse("cart_details", kwargs={"pk": self.cart.pk}))
        response = self.client.get(reverse("cart_details", kwargs={"pk": self.cart.pk}))
        self.assertNotContains(response, self.cart_item1.product.name)
        self.assertContains(response, self.cart_item2.product.name)
        self.assertContains(response, self.cart_item3.product.name)
        self.assertEqual(self.cart.cart_items.count(), 2)

    def test_change_product_count(self):
        response = self.client.post(
            reverse("cart_details", kwargs={"pk": self.cart.pk}),
            data={
                "cart_item_pk": self.cart_item1.pk,
                "save_button": "save",
                "count": 150,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.cart_item1.refresh_from_db()
        self.assertEqual(self.cart_item1.count, 1 + 149)
        self.assertEqual(self.cart_item1.product.count, 1000 - 149)
        response = self.client.get(reverse("cart_details", kwargs={"pk": self.cart.pk}))
        self.assertContains(response, self.cart_item3.count)

    def test_exceed_product_count(self):
        response = self.client.post(
            reverse("cart_details", kwargs={"pk": self.cart.pk}),
            data={
                "cart_item_pk": self.cart_item1.pk,
                "save_button": "save",
                "count": 1500,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.cart_item1.refresh_from_db()
        self.assertEqual(self.cart_item1.count, 1)
        self.assertEqual(self.cart_item1.product.count, 1000)

    def test_proceed_to_payment(self):
        response = self.client.post(
            reverse("cart_details", kwargs={"pk": self.cart.pk}),
            data={
                "cart_item_pk": self.cart_item1.pk,
                "buy_button": "buy",
                "count": 150,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            ("/transactions/transaction/" + str(self.cart.pk), 302),
            response.redirect_chain,
        )

    def test_access_other_user_cart(self):
        response = self.client.get(
            reverse(
                "cart_details",
                kwargs={"pk": self.other_user.carts.get(transaction=None).pk},
            ),
        )
        self.assertEqual(response.status_code, 404)

    def test_use_cart_as_unauthorized_user(self):
        self.client.logout()
        response = self.client.get(
            reverse(
                "cart_details",
                kwargs={"pk": self.other_user.carts.get(transaction=None).pk},
            ),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "/accounts/login/?next=/transactions/cart/", response.redirect_chain[0][0]
        )
        self.assertEquals(*response.template_name, "account/login.html")

    def test_cart_changed_to_new_one_after_transaction_assigned(self):
        cart_pk = self.cart.pk
        self.cart.delete()
        self.client.get(reverse("home"))
        self.casual_user.refresh_from_db()
        new_cart_pk = self.casual_user.carts.get(transaction=None)
        self.assertIsNotNone(cart_pk)
        self.assertNotEqual(cart_pk, new_cart_pk)

    def test_product_price(self):
        price = "20,00"
        self.assertContains(self.response, price)

    def test_negative_product_count(self):
        # TODO
        pass

    def test_access_user_pucharsed_cart(self):
        # frbidden/404
        pass


class TransactionViewTest(TestCase):
    def setUp(self):
        self.casual_user = get_user_model().objects.create(
            username="testuser",
        )
        self.casual_user.set_password("testpass123")
        self.casual_user.carts.create(transaction=None, price=None)
        self.casual_user.save()

        self.product1 = Product.objects.create(
            name="product_name1",
            producer="test_producer",
            price=100,
            count=1000,
        )
        self.product2 = Product.objects.create(
            name="product_name2",
            producer="test_producer2",
            price=200,
            count=1000,
        )
        self.product3 = Product.objects.create(
            name="product_name3",
            producer="test_producer3",
            price=300,
            count=11234,
        )

        self.cart = self.casual_user.carts.get(transaction=None)
        self.cart_item1 = self.cart.cart_items.create(product=self.product1, count=1)
        self.cart_item2 = self.cart.cart_items.create(product=self.product2, count=2)
        self.cart_item3 = self.cart.cart_items.create(product=self.product3, count=5)
        # self.cart.cart_items.add(self.cart_item1)
        # self.cart.cart_items.add(self.cart_item2)
        # self.cart.cart_items.add(self.cart_item3)

        assert self.client.login(username="testuser", password="testpass123")
        self.casual_user.addresses.create(
            address="test_address 123", city="City", postal_code="12-345"
        )
        self.response_post = self.client.post(
            reverse("transaction", kwargs={"pk": self.cart.pk}),
            data={
                "first_name": "Name",
                "last_name": "Surname",
                "radio_address": "new",
                "address": "Test st. 12",
                "city": "Test City",
                "postal_code": "11-111",
                "radio_shipping": "UPS",
                "radio_payment": "cash on delivery",
                "proceed_to_payment_button": "Proceed to payment",
                "user": self.casual_user.pk,
            },
        )
        self.response = self.client.get(
            reverse("transaction", kwargs={"pk": self.cart.pk})
        )

    def test_status_code(self):
        self.assertEqual(self.response_post.status_code, 302)
        self.assertEqual(self.response.status_code, 200)

    def test_template_used(self):
        self.assertEqual(*self.response.template_name, "transactions/transaction.html")

    def test_view_used(self):
        self.assertEqual(
            type(self.response.context_data["view"]).__name__,
            TransactionView.__name__,
        )

    def test_forms_in_context(self):
        self.assertIn("name_form", self.response.context_data)
        self.assertIn("choose_address_form", self.response.context_data)
        self.assertIn("add_new_address_form", self.response.context_data)
        self.assertIn("shipping_methods_form", self.response.context_data)
        self.assertIn("payment_methods_form", self.response.context_data)

    def test_closed_transaction(self):
        self.assertEqual(self.response_post.status_code, 302)
        self.cart.refresh_from_db()
        self.casual_user.refresh_from_db()
        self.assertIsNotNone(self.cart.transaction)
        self.assertEqual(self.casual_user.first_name, "Name")
        self.assertEqual(self.casual_user.last_name, "Surname")
        self.assertEqual(self.cart.transaction.address.address, "Test st. 12")
        self.assertEqual(self.cart.transaction.address.city, "Test City")
        self.assertEqual(self.cart.transaction.address.postal_code, "11-111")
        self.assertEqual(self.casual_user.addresses.last().address, "Test st. 12")
        self.assertEqual(self.casual_user.addresses.last().city, "Test City")
        self.assertEqual(self.casual_user.addresses.last().postal_code, "11-111")
        self.assertEqual(self.cart.transaction.shipping_method, "UPS")
        self.assertEqual(self.cart.transaction.payment_method, "cash on delivery")

    def test_new_address_created(self):
        self.assertContains(self.response, "Test st. 12")
        self.assertContains(self.response, "Test City")
        self.assertContains(self.response, "11-111")

    def test_name_last_name_placeholder(self):
        self.assertContains(self.response, 'value="Name"')
        self.assertContains(self.response, 'value="Surname"')

    def test_every_user_address_show_on_page(self):
        self.assertContains(self.response, "Test st. 12")
        self.assertContains(self.response, "Test City")
        self.assertContains(self.response, "11-111")
        self.assertContains(self.response, "test_address 123")
        self.assertContains(self.response, "City")
        self.assertContains(self.response, "12-345")

    def test_transaction_created(self):
        self.assertEqual(Transaction.objects.count(), 1)


class TransactionsUserListViewTest(TestCase):
    def setUp(self):
        self.casual_user = get_user_model().objects.create(
            username="testuser",
        )
        self.casual_user.set_password("testpass123")
        self.casual_user.carts.create(transaction=None, price=None)
        self.casual_user.save()

        self.product1 = Product.objects.create(
            name="product_name1",
            producer="test_producer",
            price=100,
            count=1000,
        )
        self.product2 = Product.objects.create(
            name="product_name2",
            producer="test_producer2",
            price=200,
            count=1000,
        )
        self.product3 = Product.objects.create(
            name="product_name3",
            producer="test_producer3",
            price=300,
            count=11234,
        )

        self.cart = self.casual_user.carts.get(transaction=None)
        self.cart_item1 = self.cart.cart_items.create(product=self.product1, count=1)
        self.cart_item2 = self.cart.cart_items.create(product=self.product2, count=2)
        self.cart_item3 = self.cart.cart_items.create(product=self.product3, count=5)

        assert self.client.login(username="testuser", password="testpass123")
        self.casual_user.addresses.create(
            address="test_address 123", city="City", postal_code="12-345"
        )
        self.response_post = self.client.post(
            reverse("transaction", kwargs={"pk": self.cart.pk}),
            data={
                "first_name": "Name",
                "last_name": "Surname",
                "radio_address": "new",
                "address": "Test st. 12",
                "city": "Test City",
                "postal_code": "11-111",
                "radio_shipping": "UPS",
                "radio_payment": "cash on delivery",
                "proceed_to_payment_button": "Proceed to payment",
                "user": self.casual_user.pk,
            },
        )
        self.transaction = Transaction.objects.last()

        self.casual_user.carts.create(transaction=None, price=None)
        self.cart2 = self.casual_user.carts.get(transaction=None)
        self.cart_item1 = self.cart2.cart_items.create(product=self.product1, count=10)
        self.cart_item2 = self.cart2.cart_items.create(product=self.product2, count=20)
        self.casual_user.addresses.create(
            address="test_address 123", city="City", postal_code="12-345"
        )
        self.response_post2 = self.client.post(
            reverse("transaction", kwargs={"pk": self.cart.pk}),
            data={
                "first_name": "Name2",
                "last_name": "Surname2",
                "radio_address": "new",
                "address": "Other st. 12",
                "city": "Other City",
                "postal_code": "121-1311",
                "radio_shipping": "UPS",
                "radio_payment": "cash on delivery",
                "proceed_to_payment_button": "Proceed to payment",
                "user": self.casual_user.pk,
            },
        )
        self.response = self.client.get(reverse("transaction_history"))
        self.transaction2 = Transaction.objects.last()

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_template_used(self):
        self.assertEqual(
            self.response.template_name[0], "transactions/transaction_history.html"
        )

    def test_view_used(self):
        self.assertEqual(
            type(self.response.context_data["view"]).__name__,
            TransactionsUserListView.__name__,
        )

    def test_every_transaction_show_on_page(self):
        self.assertContains(self.response, "Date")
        self.assertContains(self.response, "Products")
        self.assertContains(self.response, self.product1.name)
        self.assertContains(self.response, self.product2.name)
        self.assertContains(self.response, self.product3.name)
        self.assertContains(self.response, "Address")
        self.assertContains(self.response, self.transaction.address.address)
        self.assertContains(self.response, self.transaction2.address.address)
        self.assertContains(self.response, self.transaction.address.city)
        self.assertContains(self.response, self.transaction2.address.city)
        self.assertContains(self.response, self.transaction.address.postal_code)
        self.assertContains(self.response, self.transaction2.address.postal_code)
        self.assertContains(self.response, "Shipping Method")
        self.assertContains(self.response, self.transaction.shipping_method)
        self.assertContains(self.response, self.transaction2.shipping_method)
