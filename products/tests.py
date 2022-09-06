from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse, resolve
from .models import Product, Category
from .views import SearchResultView
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from products.views import (
    CategoryDetailsView,
    CategoryListView,
    CategoryManageProductsView,
)
import requests


class ProductTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Hoe",
            producer="Universe",
            price=25,
            description="Test One",
            count=1000,
        )
        Product.objects.create(
            name="Scythe",
            producer="Other Universe",
            price=125,
            description="Test Two",
            count=100,
        )
        self.user = get_user_model().objects.create(
            username="productuser", is_staff=True
        )
        self.user.set_password("testpass123")
        self.user.save()

    def test_product_list(self):
        self.assertEqual(f"{self.product.name}", "Hoe")
        self.assertEqual(f"{self.product.producer}", "Universe")
        self.assertEqual(f"{self.product.price}", "25")

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
                "price": 1234,
                "count": 1000,
            },
            follow=True,
        )
        product = Product.objects.get(
            name="kosiarka",
            producer="Sztil",
            price=1234,
            count=1000,
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
    @classmethod
    def setUpTestData(self):
        self.product = Product.objects.create(
            name="Hoe",
            producer="Universe",
            price=25,
            description="Test One",
            count=1000,
        )

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

        self.url = reverse("images_manager", kwargs={"pk": self.product.pk})

        # images to test upload
        self.images = list()
        for i in range(5):
            res = requests.get("https://picsum.photos/200/300", stream=True)
            image = SimpleUploadedFile(
                f"image{i}.jpg", res.content, content_type="image/jpeg"
            )
            self.images.append(image)
        self.image = self.images[0]

        # Initial images in test db
        for i in range(5):
            res = requests.get("https://picsum.photos/200/300", stream=True)
            self.product.images.create(
                image=SimpleUploadedFile(
                    f"image{i}.jpg", res.content, content_type="image/jpeg"
                ),
                place=i,
            )

    def test_use_manager_as_unauthorized_user(self):
        self.client.logout()
        response = self.client.get(
            self.url,
            follow=True,
        )
        self.assertContains(response, "Sign In")
        self.assertEquals(
            response.wsgi_request.path,
            reverse("account_login"),
        )
        self.assertEquals(
            *response.redirect_chain,
            (reverse("account_login") + "?next=" + self.url, 302),
        )
        assert "next" in response.wsgi_request.GET
        self.assertEqual(response.wsgi_request.GET.get("next"), self.url)
        self.assertEqual(response.wsgi_request.resolver_match.url_name, "account_login")

    def test_manage_images_as_casual_user(self):
        assert self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            self.url,
            follow=True,
        )
        self.assertEquals(response.status_code, 403)
        self.assertEquals(response.reason_phrase, "Forbidden")

    def test_upload_image(self):
        assert self.client.login(username="staffuser", password="testpass123")
        images_count = self.product.images.count()
        response = self.client.post(
            self.url,
            data={
                "upload_images": "upload_images",
                "image": self.image,
                "product_pk": self.product.pk,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.product.images.count(), images_count + 1)
        self.product.images.all().delete()

    def test_upload_multiple_images(self):
        assert self.client.login(username="staffuser", password="testpass123")
        images_count = self.product.images.count()
        response = self.client.post(
            self.url,
            data={
                "upload_images": "upload_images",
                "image": self.images,
                "product_pk": self.product.pk,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.product.images.count(), images_count + 5)

    def test_upload_non_image(self):
        assert self.client.login(username="staffuser", password="testpass123")
        txt_file = SimpleUploadedFile(
            "file.txt", b"some text", content_type="text/plain"
        )
        images_count = self.product.images.count()
        response = self.client.post(
            self.url,
            data={
                "upload_images": "upload_images",
                "image": txt_file,
                "product_pk": self.product.pk,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.product.images.count(), images_count)

    def test_delete_image(self):
        assert self.client.login(username="staffuser", password="testpass123")
        images_count = self.product.images.count()
        response = self.client.post(
            self.url,
            data={"image_pk": self.product.images.last().pk, "delete": "delete"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.product.images.count(), images_count - 1)

    def test_change_images_order(self):
        assert self.client.login(username="staffuser", password="testpass123")
        image = self.product.images.last()
        images_count = self.product.images.count()
        self.assertEqual(image.place, images_count - 1)
        response = self.client.post(
            self.url,
            data={"image_pk": image.pk, "move_up": "move_up"},
            follow=True,
        )
        image.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(image.place, images_count - 2)
        response = self.client.post(
            self.url,
            data={"image_pk": image.pk, "move_down": "move_down"},
            follow=True,
        )
        image.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(image.place, images_count - 1)

        # border values
        # border value down
        for i in range(2):
            response = self.client.post(
                self.url,
                data={"image_pk": image.pk, "move_down": "move_down"},
                follow=True,
            )
        image.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(image.place, images_count - 1)

        # border value up
        for i in range(images_count + 2):
            response = self.client.post(
                self.url,
                data={"image_pk": image.pk, "move_up": "move_up"},
                follow=True,
            )
        image.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(image.place, 0)

        # places don't repeat
        self.assertEqual(
            len(set(self.product.images.values_list("place", flat=True))), images_count
        )


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
