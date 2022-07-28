from django.test import TestCase
from django.contrib.auth import get_user_model
from products.models import Product
from .models import Review


class ReviewTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="reviewuser",
            emal="test@testmail.com",
            password="testpassword123",
        )
        self.product = Product.objects.create(
            name="testitem",
            producer="testcompany",
            price="2.5",
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

    def test_review_in_product_details_view(self):
        response = self.client.get(self.product.get_absolute_url())
        self.assertContains(response, "testitem", status_code=200)
        self.assertContains(response, "test review", 2)
        self.assertContains(response, "reviewuser")
