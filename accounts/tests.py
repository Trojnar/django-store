from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse, resolve
from .models import CustomUser
from allauth.account.views import SignupView
import time


class CustomUserTests(TestCase):
    def setUp(self):
        self.User = get_user_model()

    def test_user_is_custom_user_instance(self):
        self.assertEqual(self.User, CustomUser)

    def test_create_user(self):
        user = self.User.objects.create_user(
            username="will",
            email="will@email.com",
            password="testpass123",
        )
        self.assertEqual(user.username, "will")
        self.assertEqual(user.email, "will@email.com")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        admin_user = self.User.objects.create_superuser(
            username="superadmin",
            email="superadmin@email.com",
            password="testpass123",
        )
        self.assertEqual(admin_user.username, "superadmin")
        self.assertEqual(admin_user.email, "superadmin@email.com")
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)


class SignupPageTests(TestCase):
    def setUp(self):
        self.url = reverse("account_signup")
        self.response = self.client.get(self.url)

    def test_signup_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_signup_template_contains(self):
        self.assertContains(self.response, "Sign Up")

    def test_signup_template_not_contains(self):
        self.assertNotContains(self.response, "shouldn't be here")

    def test_signup_template_used(self):
        self.assertTemplateUsed(self.response, "account/signup.html")

    def test_create_user_status_code(self):
        self.client.logout()
        response_pswrd_crrct = self.client.post(
            self.url,
            data={
                "email": "testmail@test.com",
                "username": "test_user",
                "password1": "test_password",
                "password2": "test_password",
            },
        )
        self.assertEqual(response_pswrd_crrct.status_code, 302)
        self.assertTrue(get_user_model().objects.filter(username="test_user").exists())

    def test_create_user_with_wrong_passwod_confirmation(self):
        self.client.logout()
        response_psswrd_incrrct = self.client.post(
            self.url,
            data={
                "email": "testmail2@test.com",
                "username": "test_user2",
                "password1": "test_password",
                "password2": "different_password",
            },
            follow=True,
        )
        self.assertContains(
            response_psswrd_incrrct,
            "You must type the same password each time.",
            status_code=200,
        )

    def test_incorrect_data_user_created_db(self):
        self.assertFalse(
            get_user_model().objects.filter(username="test_user2").exists()
        )

    def test_redirect_to_homepage_after_signup(self):
        response = self.client.post(
            self.url,
            data={
                "email": "testmail3@test.com",
                "username": "test_user3",
                "password1": "test_password",
                "password2": "test_password",
            },
            follow=True,
        )
        self.assertTemplateUsed(response, "home.html")
        self.assertEqual(response.redirect_chain[0][0], "/")

    def test_signup_view(self):
        view = resolve("/accounts/signup/")
        self.assertEqual(view.func.__name__, SignupView.as_view().__name__)


class AccountSettingsViewTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="casualuser", email="casualuser@email.com", password="testpass123"
        )
        self.is_logged_in = self.client.login(
            username="casualuser", password="testpass123"
        )

    def test_for_logged_in_user(self):
        self.is_logged_in = self.client.login(
            username="casualuser", password="testpass123"
        )
        self.assertTrue(self.is_logged_in)
        response = self.client.get(reverse("account_settings"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/settings.html")
        self.assertContains(
            response,
            '<a href="%s">Change password</a>' % reverse("account_change_password"),
            html=True,
        )
        self.assertContains(
            response,
            '<a href="%s">Reset password</a>' % reverse("account_reset_password"),
            html=True,
        )
        self.assertContains(
            response,
            '<a href="%s">Manage e-mail</a>' % reverse("account_email"),
            html=True,
        )
        self.assertContains(
            response,
            '<a href="%s">Manage socials</a>' % reverse("socialaccount_connections"),
            html=True,
        )

    def test_for_not_logged_in_user(self):
        self.client.logout()
        response = self.client.get(reverse("account_settings"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            "%s?next=/accounts/settings/" % reverse("account_login"),
        )
        response = self.client.get(reverse("account_login"))
        self.assertContains(response, "Log In")
