from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse, resolve
from .models import Product
from .views import SearchResultView
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission


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
        self.user = get_user_model().objects.create(
            username="productuser", is_staff=True
        )
        self.user.set_password("testpass123")
        self.user.save()

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
        no_response = self.client.get("/products/randomurljfsdljkfsa/")
        self.assertEqual(no_response.status_code, 404)
        self.assertContains(response, "Hoe", status_code=200)
        self.assertContains(response, "Universe")
        self.assertTemplateUsed("product_details.html")

    def test_product_list_for_logged_out_user(self):
        self.client.logout()
        response = self.client.get(reverse("product_list"))
        self.assertEqual(response.status_code, 200)

    def test_create_product_as_unauthorized_user(self):
        self.client.logout()
        response = self.client.get(reverse("product_create"))
        self.assertRedirects(
            response, f"{reverse('account_login')}?next={reverse('product_create')}"
        )

    def test_create_product_as_casual_user(self):
        self.client.login(username="productuser", password="testpass123")
        response = self.client.get(reverse("product_create"))
        self.assertEqual(response.status_code, 403)

    def test_create_product_as_staff_member(self):
        group = Group.objects.create(name="Staff")
        group.permissions.add(Permission.objects.get(codename="add_product"))
        self.user.groups.add(group)
        self.client.login(username="productuser", password="testpass123")
        response = self.client.get(reverse("product_create"))
        self.assertContains(response, "Create Product", status_code=200)
        self.assertTemplateUsed("product_details.html")
        response = self.client.post(
            reverse("product_create"),
            data={
                "name": "kosiarka",
                "producer": "Sztil",
                "price": "1234",
            },
            follow=True,
        )
        product = Product.objects.get(
            name="kosiarka",
            producer="Sztil",
            price="1234",
        )
        self.assertTrue(product)
        self.assertRedirects(
            response, reverse("product_details", kwargs={"pk": product.pk})
        )
        self.assertTemplateUsed(response, "product_details.html")

    def test_reviews_form_exists_at_product_details(self):
        assert self.client.login(username="productuser", password="testpass123")
        response = self.client.get(
            reverse("product_details", kwargs={"pk": self.product.pk}),
        )
        self.assertContains(
            response, '<form action="" method="post">\n', status_code=200
        )

    def test_search_form_exists(self):
        response = self.client.get(
            reverse("product_details", kwargs={"pk": self.product.pk}),
        )
        self.assertContains(
            response,
            '<input name="phrase" type="text" placeholder="Search...">',
            status_code=200,
        )

    def test_details_product_review_as_unauthorized_user(self):
        self.client.logout()
        response = self.client.get(
            reverse(
                "product_details",
                kwargs={"pk": self.product.pk},
            )
        )
        self.assertContains(response, "Only logged in users can add reviews.")

    def test_details_product_review_form(self):
        assert self.client.login(username="productuser", password="testpass123")
        response = self.client.post(
            reverse("product_details", kwargs={"pk": self.product.pk}),
            data={"review": "This review was created on details product page."},
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse("product_details", kwargs={"pk": self.product.pk}),
        )


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
