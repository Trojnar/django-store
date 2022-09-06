from products.models import get_product_model
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
import requests


# Create your tests here.
# Images app test
class ImageManager(TestCase):
    @classmethod
    def setUpTestData(self):
        self.product = get_product_model().objects.create(
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
