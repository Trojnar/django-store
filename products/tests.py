from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse, resolve
from .models import Product
from .views import SearchResultView
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
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
