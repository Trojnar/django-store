from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from products.models import Product
from .models import Review


class ReviewTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="reviewuser",
            email="test@testmail.com",
            password="testpassword123",
        )
        self.product = Product.objects.create(
            name="testitem",
            producer="testcompany",
            price="25",
            count=1000,
        )
        self.review = Review.objects.create(
            author=self.user,
            product=self.product,
            review="test review",
        )
        self.other_review = Review.objects.create(
            author=self.user,
            product=self.product,
            review="test review",
        )
        self.create_review_url = reverse(
            "review_create",
            kwargs={"pk": self.product.pk},
        )

    def test_review_in_product_details_view(self):
        response = self.client.get(self.product.get_absolute_url())
        self.assertContains(response, "testitem", status_code=200)
        self.assertContains(response, "test review", 2)
        self.assertContains(response, "reviewuser")

    def test_review_view(self):
        is_logged_in = self.client.login(
            username="reviewuser",
            password="testpassword123",
        )
        self.assertTrue(is_logged_in)
        response = self.client.post(
            self.create_review_url,
            data={
                "review": "This product is awesome!",
            },
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                "product_details",
                kwargs={"pk": self.product.pk},
            ),
        )
        response_product_details = self.client.get(
            reverse(
                "product_details",
                kwargs={"pk": self.product.pk},
            )
        )
        self.assertContains(response_product_details, "This product is awesome!")
        self.assertContains(response_product_details, "reviewuser")

    def test_unauthorized_creation_view(self):
        self.client.logout()
        response_logout = self.client.get(self.create_review_url)
        self.assertRedirects(
            response_logout,
            reverse("account_login")
            + "?next="
            + reverse(
                "review_create",
                kwargs={"pk": self.product.pk},
            ),
        )
