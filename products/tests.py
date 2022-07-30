import re
from django.test import TestCase
from django.urls import reverse, resolve
from .models import Product
from .views import SearchResultView


class ProductTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Hoe",
            producer="Universe",
            price=2.5,
        )
        Product.objects.create(
            name="Scythe",
            producer="Other Universe",
            price=12.5,
        )

    def test_product_list(self):
        self.assertEqual(f"{self.product.name}", "Hoe")
        self.assertEqual(f"{self.product.producer}", "Universe")
        self.assertEqual(f"{self.product.price}", "2.5")

    def test_product_list_view(self):
        response = self.client.get(reverse("product_list"))
        self.assertContains(response, "Hoe", status_code=200)
        self.assertContains(response, "Scythe")
        self.assertTemplateUsed("product_list.html")

    def test_product_details_view(self):
        response = self.client.get(self.product.get_absolute_url())
        no_response = self.client.get("/products/0/")
        self.assertEqual(no_response.status_code, 404)
        self.assertContains(response, "Hoe", status_code=200)
        self.assertContains(response, "Universe")
        self.assertTemplateUsed("product_details.html")

    def test_product_list_for_logged_out_user(self):
        self.client.logout()
        response = self.client.get(reverse("product_list"))
        self.assertEqual(response.status_code, 200)


class SearchResultViewTest(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Hoe",
            producer="Universe",
            price=2.5,
        )
        self.product2 = Product.objects.create(
            name="Scythe",
            producer="Some producer",
            price=12.5,
        )
        self.product3 = Product.objects.create(
            name="Scythe",
            producer="Hoe",
            price=1234.5,
        )
        self.response = self.client.get(reverse("search_result"))

    def test_search_results_view(self):
        view = resolve("/products/search/")
        self.assertEqual(SearchResultView.as_view().__name__, view.func.__name__)

    def test_search_results_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_search_results_template(self):
        self.assertTemplateUsed(self.response, "search_result.html")

    def test_search_results_contains(self):
        response = self.client.get(reverse("search_result"), {"phrase": "scythe"})
        self.assertContains(response, "Scythe")
        self.assertContains(response, "Hoe")
        self.assertNotContains(response, "Universe")

        response = self.client.get(reverse("search_result"), {"phrase": "producer"})
        self.assertContains(response, "Scythe")
        self.assertContains(response, "Some producer")
        self.assertNotContains(response, "Hoe")

        response = self.client.get("/products/search/?phrase=")
        self.assertContains(response, "No results to show.")

        response = self.client.get(reverse("search_result"), {"phrase": " "})
        self.assertContains(response, "No results to show.")

    def test_search_input_on_homepage(self):
        response = self.client.get(reverse("home"))
        self.assertContains(
            response, '<input name="phrase" type="text" placeholder="Search...">'
        )
