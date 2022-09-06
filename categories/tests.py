from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from .models import Product, Category
from .views import (
    CategoryDetailsView,
    CategoryListView,
    CategoryManageProductsView,
)
import requests


# Create your tests here.
# Categories app test
class CategoryListViewTest(TestCase):
    def setUp(self):
        casual_user = get_user_model().objects.create(
            username="testuser",
        )
        casual_user.set_password("testpass123")
        casual_user.save()

        self.staff_user = get_user_model().objects.create(
            username="staffuser",
            is_staff=True,
        )
        self.staff_user.set_password("testpass123")
        self.staff_user.save()

        self.category = Category.objects.create(
            name="test category",
        )
        product1 = Product.objects.create(
            name="name",
            producer="test_producer",
            price=123,
            count=1000,
        )
        product2 = Product.objects.create(
            name="name2",
            producer="test_producer2",
            price=321,
            count=1000,
        )
        self.category.products.add(product1)
        self.category.products.add(product2)
        assert self.client.login(username="staffuser", password="testpass123")
        self.response = self.client.get(reverse("category_list"))

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_used_view(self):
        self.assertEqual(self.response.template_name, "category_details.html")

    def test_used_view(self):
        self.assertEqual(
            type(self.response.context["view"]).__name__,
            CategoryListView.__name__,
        )

    def test_buttons_in_template(self):
        self.assertContains(self.response, "category_delete")

    def test_category_forms(self):
        response = self.client.post(
            reverse("category_list"),
            data={"category_create": "Add Category"},
        )
        self.assertEquals(response.status_code, 200)
        assert "category_create_form" in response.context
        self.assertContains(response, "submit_category_create")

        response = self.client.post(
            reverse("category_list"),
            data={"category_update": "edit", "category_pk": self.category.pk},
        )
        assert "category_update_form" in response.context
        self.assertContains(response, "submit_category_update")

    def test_create_category(self):
        category_count = Category.objects.count()
        response = self.client.post(
            reverse("category_list"),
            data={"name": "new_category", "submit_category_create": "Submit"},
        )
        self.assertContains(response, "new_category", status_code=200)
        self.assertEqual(Category.objects.count(), category_count + 1)

    def test_edit_category(self):
        response = self.client.post(
            reverse("category_list"),
            data={
                "name": "edited_category",
                "category_pk": self.category.pk,
                "submit_category_update": "submit",
            },
        )
        self.assertContains(response, "edited_category", status_code=200)

    def test_delete_category(self):
        category_count = Category.objects.count()
        response = self.client.post(
            reverse("category_list"),
            data={
                "category_delete": "delete",
                "category_pk": self.category.pk,
            },
        )
        self.assertEqual(Category.objects.count(), category_count - 1)
        self.assertNotContains(response, self.category.name, status_code=200)

    def test_no_cud_as_casual_user(self):
        self.client.logout()
        assert self.client.login(username="testuser", password="testpass123")
        # read
        response = self.client.get(reverse("category_list"))
        self.assertContains(self.response, self.category.name, status_code=200)

        # delete
        category_count = Category.objects.count()
        response = self.client.post(
            reverse("category_list"),
            data={
                "category_delete": "delete",
                "category_pk": self.category.pk,
            },
        )
        self.assertEqual(Category.objects.count(), category_count)
        self.assertNotContains(response, self.category.name, status_code=403)

        # update
        response = self.client.post(
            reverse("category_list"),
            data={
                "name": "edited_category",
                "category_pk": self.category.pk,
                "submit_category_update": "submit",
            },
        )
        self.assertNotContains(response, "edited_category", status_code=403)

        # create
        response = self.client.post(
            reverse("category_list"),
            data={"name": "new_category", "submit_category_create": "Submit"},
        )
        self.assertNotContains(response, "new_category", status_code=403)
        self.assertEqual(Category.objects.count(), category_count)

    def test_read_as_unauthorized_user(self):
        self.response = self.client.get(reverse("category_list"))
        self.assertContains(self.response, self.category.name, status_code=200)


class CategoryDetailsViewTest(TestCase):
    def setUp(self):
        casual_user = get_user_model().objects.create(
            username="testuser",
        )
        casual_user.set_password("testpass123")
        casual_user.save()

        staff_user = get_user_model().objects.create(
            username="staffuser",
            is_staff=True,
        )
        staff_user.set_password("testpass123")
        staff_user.save()

        self.category = Category.objects.create(
            name="test category",
        )
        self.product1 = Product.objects.create(
            name="product_name",
            producer="test_producer",
            price=123,
            count=1000,
        )
        self.product2 = Product.objects.create(
            name="product_name2",
            producer="test_producer2",
            price=321,
            count=1000,
        )
        self.product3 = Product.objects.create(
            name="product_name2",
            producer="test_producer2",
            price=1,
            count=1000,
        )
        self.category.products.add(self.product1)
        self.category.products.add(self.product2)
        self.category.products.add(self.product3)
        assert self.client.login(username="testuser", password="testpass123")
        self.response = self.client.get(
            reverse("category_details", kwargs={"pk": self.category.pk})
        )

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_used_template(self):
        self.assertEqual(*self.response.template_name, "category_details.html")

    def test_used_view(self):
        self.assertEqual(
            type(self.response.context["view"]).__name__,
            CategoryDetailsView.__name__,
        )

    def test_category_in_context(self):
        assert "category" in self.response.context_data

    def test_template_content_contains(self):
        self.assertContains(self.response, self.product1.name)
        self.assertContains(self.response, self.product2.name)
        self.assertContains(self.response, self.product1.producer)
        self.assertContains(self.response, self.product2.producer)
        self.assertContains(self.response, str(self.product1.count) + " left.")
        self.assertContains(self.response, "cart_add_button", count=3)

    def test_add_to_cart(self):
        product_count = self.product1.count
        self.response = self.client.post(
            reverse(
                "category_details",
                kwargs={
                    "pk": self.category.pk,
                },
            ),
            data={
                "cart_add_button": "Add to cart",
                "product_pk": self.product1.pk,
            },
        )
        self.product1.refresh_from_db()
        self.assertEqual(product_count - 1, self.product1.count)
        self.assertContains(self.response, str(self.product1.count) + " left.")

    def test_add_to_cart_as_unauthorized_user(self):
        self.client.logout()
        self.assertNotContains(self.response, "category_add_button")
        product_count = self.product1.count
        response = self.client.post(
            reverse(
                "category_details",
                kwargs={
                    "pk": self.category.pk,
                },
            ),
            data={
                "cart_add_button": "Add to cart",
                "product_pk": self.product1.pk,
            },
        )
        self.product1.refresh_from_db()
        self.assertEqual(product_count, self.product1.count)
        self.assertContains(self.response, str(self.product1.count) + " left.")

    def test_price_formatting(self):
        self.assertContains(
            self.response,
            str(self.product1.price)[:-2] + "," + str(self.product1.price)[-2:],
        )
        self.assertContains(
            self.response,
            str(self.product2.price)[:-2] + "," + str(self.product2.price)[-2:],
        )
        self.assertContains(
            self.response,
            "0,01",
        )


class CategoryManageProductsViewTest(TestCase):
    def setUp(self):
        casual_user = get_user_model().objects.create(
            username="testuser",
        )
        casual_user.set_password("testpass123")
        casual_user.save()

        self.staff_user = get_user_model().objects.create(
            username="staffuser",
            is_staff=True,
        )
        self.staff_user.set_password("testpass123")
        self.staff_user.save()

        self.category = Category.objects.create(
            name="test category",
        )
        self.product1 = Product.objects.create(
            name="name",
            producer="test_producer",
            price=123,
            count=1000,
        )
        self.product2 = Product.objects.create(
            name="name2",
            producer="test_producer2",
            price=321,
            count=1000,
        )
        self.product3 = Product.objects.create(
            name="name2",
            producer="test_producer2",
            price=321,
            count=1000,
        )
        assert self.client.login(username="staffuser", password="testpass123")
        self.response = self.client.get(
            reverse("category_checkbox", kwargs={"pk": self.category.pk})
        )

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_used_view(self):
        self.assertEqual(self.response.template_name, "category_checkbox.html")

    def test_used_view(self):
        self.assertEqual(
            type(self.response.context["view"]).__name__,
            CategoryManageProductsView.__name__,
        )

    def test_category_name_on_page(self):
        self.assertContains(self.response, self.category.name)

    def test_forms_in_context_data(self):
        self.assertIn("form_addable", self.response.context_data)
        self.assertIn("form_already_added", self.response.context_data)

    def test_products_to_assign(self):
        choices = self.response.context_data["form_addable"].fields["choices"].choices
        self.assertIn((self.product1.pk, self.product1.name), choices)
        self.assertIn((self.product2.pk, self.product2.name), choices)
        self.assertIn((self.product3.pk, self.product3.name), choices)

    def test_product_already_assigned(self):
        self.category.products.add(self.product1)
        self.category.products.add(self.product2)
        response = self.client.get(
            reverse("category_checkbox", kwargs={"pk": self.category.pk})
        )
        choices = response.context_data["form_already_added"].fields["choices"].choices
        self.assertIn((self.product1.pk, self.product1.name), choices)
        self.assertIn((self.product2.pk, self.product2.name), choices)

    def test_assign_product(self):
        response = self.client.post(
            reverse("category_checkbox", kwargs={"pk": self.category.pk}),
            data={
                "choices": [self.product1.pk],
                "add_button": "Add",
            },
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            reverse("category_checkbox", kwargs={"pk": self.category.pk})
        )
        choices = response.context_data["form_already_added"].fields["choices"].choices
        self.assertIn((self.product1.pk, self.product1.name), choices)
        self.assertEqual(self.category.products.count(), 1)

    def test_assign_multiple_products(self):
        response = self.client.post(
            reverse("category_checkbox", kwargs={"pk": self.category.pk}),
            data={
                "choices": [self.product1.pk, self.product3.pk],
                "add_button": "Add",
            },
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            reverse("category_checkbox", kwargs={"pk": self.category.pk})
        )
        choices = response.context_data["form_already_added"].fields["choices"].choices
        self.assertIn((self.product1.pk, self.product1.name), choices)
        self.assertIn((self.product3.pk, self.product3.name), choices)
        self.assertNotIn((self.product2.pk, self.product2.name), choices)
        choices = response.context_data["form_addable"].fields["choices"].choices
        self.assertNotIn((self.product1.pk, self.product1.name), choices)
        self.assertNotIn((self.product3.pk, self.product3.name), choices)
        self.assertIn((self.product2.pk, self.product2.name), choices)
        self.assertEqual(self.category.products.count(), 2)

    def test_unassign_product(self):
        self.category.products.add(self.product2)
        self.category.products.add(self.product3)
        response = self.client.post(
            reverse("category_checkbox", kwargs={"pk": self.category.pk}),
            data={
                "choices": [self.product2.pk],
                "delete_button": "Delete",
            },
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            reverse("category_checkbox", kwargs={"pk": self.category.pk})
        )
        choices = response.context_data["form_addable"].fields["choices"].choices
        self.assertIn((self.product2.pk, self.product2.name), choices)
        self.assertIn((self.product1.pk, self.product1.name), choices)
        self.assertNotIn((self.product3.pk, self.product3.name), choices)
        choices = response.context_data["form_already_added"].fields["choices"].choices
        self.assertIn((self.product3.pk, self.product3.name), choices)
        self.assertNotIn((self.product2.pk, self.product2.name), choices)
        self.assertNotIn((self.product1.pk, self.product1.name), choices)
        self.assertEqual(self.category.products.count(), 1)

    def test_unassign_multiple_products(self):
        self.category.products.add(self.product2)
        self.category.products.add(self.product3)
        response = self.client.post(
            reverse("category_checkbox", kwargs={"pk": self.category.pk}),
            data={
                "choices": [self.product2.pk, self.product3.pk],
                "delete_button": "Delete",
            },
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            reverse("category_checkbox", kwargs={"pk": self.category.pk})
        )
        choices = response.context_data["form_addable"].fields["choices"].choices
        self.assertIn((self.product2.pk, self.product2.name), choices)
        self.assertIn((self.product1.pk, self.product1.name), choices)
        self.assertIn((self.product3.pk, self.product3.name), choices)
        choices = response.context_data["form_already_added"].fields["choices"].choices
        self.assertNotIn((self.product3.pk, self.product3.name), choices)
        self.assertNotIn((self.product2.pk, self.product2.name), choices)
        self.assertNotIn((self.product1.pk, self.product1.name), choices)
        self.assertEqual(self.category.products.count(), 0)

    def test_unauthorized_user_redirect_to_login_page(self):
        self.client.logout()
        response = self.client.get(
            reverse("category_checkbox", kwargs={"pk": self.category.pk})
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.get(
            reverse("category_checkbox", kwargs={"pk": self.category.pk}), follow=True
        )
        self.assertContains(response, "Sign In", status_code=200)
        self.assertEquals(*response.template_name, "account/login.html")

    def test_use_as_casual_user(self):
        self.client.logout()
        assert self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            reverse("category_checkbox", kwargs={"pk": self.category.pk}),
            data={
                "choices": [self.product1.pk],
                "add_button": "Add",
            },
        )
        self.assertEqual(response.status_code, 403)
