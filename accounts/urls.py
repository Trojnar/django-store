from django.urls import path
from .views import SignUpView, AccountSettingsView, AddressManage

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("settings/", AccountSettingsView.as_view(), name="account_settings"),
    path("addresses/", AddressManage.as_view(), name="address_manage"),
]
