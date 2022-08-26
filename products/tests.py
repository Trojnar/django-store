from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse, resolve
from .models import Product, Categorie
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

    def test_update_data_on_details_page(self):
        pass

    def test_photos_display_on_details_page(self):
        pass

    def test_create_product(self):
        pass

    def test_create_product_with_images(self):
        pass

    def test_create_product_as_casual_user(self):
        pass

    def test_create_product_as_staff_user(self):
        pass

    def test_template_used_for_create_product_page(self):
        pass

    def test_edit_review_as_casual_user(self):
        pass

    def test_edit_review_as_staff_user(self):
        pass

    def test_add_to_cart_button(self):
        pass

    def test_categories_form_on_crete_product(self):
        pass


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


# Images app test
class ImageManager(TestCase):
    def setUp(self):
        pass

    def test_use_manager_as_unauthorized_user(self):
        pass

    def test_delete_image(self):
        pass

    def test_change_images_order(self):
        pass

    def test_upload_images(self):
        pass

    def test_manage_images_as_casual_user(self):
        pass


# Categories app test
class CategorieDetailsViewTest(TestCase):
    def setUp(self):
        category = Categorie.objects.create(
            name="test categorie",
        )
        product1 = Product.objects.create(
            name="name",
            producer="test_producer",
            price=123,
        )
        product2 = Product.objects.create(
            name="name2",
            producer="test_producer2",
            price=321,
        )
        category.products.add(product1)
        category.products.add(product2)

    def test_status_code(self):
        response = self.client.get(reverse("categorie_details", kwargs={"pk": 1}))

    def test_template_used(self):
        pass

    def test_view_used(self):
        pass

    def test_buttons_in_context(self):
        pass

    def test_add_categorie_form(self):
        pass

    def test_create_categorie(self):
        pass

    def test_edit_categorie_form(self):
        pass

    def test_edit_categorie(self):
        pass

    def test_delete_categorie(self):
        pass

    def test_no_crud_as_casual_user(self):
        pass


class CategorieDetailsView(TestCase):
    def setUp(self):
        pass

    def test_status_code(self):
        pass

    def test_template_used(self):
        pass

    def test_view_used(self):
        pass

    def test_add_to_cart_button(self):
        pass


class CheckboxViewTest(TestCase):
    def setUp(self):
        pass

    def test_status_code(self):
        pass

    def test_template_used(self):
        pass

    def test_view_used(self):
        pass

    def test_can_assign_relationship(self):
        pass

    def test_can_unassign_relationship(self):
        pass


class CategorieManageProductsView(TestCase):
    def setUp(self):
        pass

    def test_status_code(self):
        pass

    def test_template_used(self):
        pass

    def test_view_used(self):
        pass

    def test_categorie_name_on_page(self):
        pass

    def test_products_to_assign(self):
        pass

    def test_product_already_assigned(self):
        pass

    def test_assign_product(self):
        pass

    def test_unassign_product(self):
        pass


# Transaction app tests
class CartViewTest(TestCase):
    def setUp(self):
        pass

    def test_status_code(self):
        pass

    def test_template_used(self):
        pass

    def test_view_used(self):
        pass

    def test_delete_product_from_cart(self):
        pass

    def test_change_product_count(self):
        pass

    def test_proceed_to_payment(self):
        pass

    def test_use_cart_as_unauthorized_user(self):
        pass

    def test_cart_changed_to_new_one_after_transaction_assigned(self):
        pass


class TransactionViewTest(TestCase):
    def setUp(self):
        pass
        # response = self.client.post(reverse('transaction', kwargs={'pk': 21}), data={'first_name': 'Lucek', 'last_name': 'twoj stary', 'radio_addresses': 'new', 'city': 'sadf', 'postal_code':'123', 'address': 'asdf', 'radio_payment': 'payment_1'})
        # response = self.client.post(reverse('transaction', kwargs={'pk': 21}), data={'first_name': 'Lucek', 'last_name': 'twoj stary', 'radio_addresses': 'new', 'city': '', 'postal_code':'123', 'address': 'asdf', 'radio_payment': 'payment_1'})

    def test_status_code(self):
        pass

    def test_template_used(self):
        pass

    def test_view_used(self):
        pass

    def test_name_form_in_context(self):
        pass

    def test_name_form(self):
        pass

    def test_address_form_in_context(self):
        pass

    def test_new_address_created(self):
        pass

    def test_shipping_method_form_in_context(self):
        pass

    def test_payment_method_form_in_context(self):
        pass

    def test_every_user_address_show_on_page(self):
        pass

    def test_user_have_no_addresses_assigned(self):
        pass

    def test_create_new_address_blank_form(self):
        pass

    def test_transaction_created(self):
        pass


class TransactionsUserListViewTest(TestCase):
    def setUp(self):
        pass

    def test_status_code(self):
        pass

    def test_template_used(self):
        pass

    def test_view_used(self):
        pass

    def test_every_transaction_show_on_page(self):
        pass
