from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from django.db.models.query import QuerySet

from accounts.models import Address


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = (
            "email",
            "username",
        )


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = get_user_model()
        fields = (
            "email",
            "username",
        )


class CustomUserNameForm(UserChangeForm):
    password = None

    class Meta:
        model = get_user_model()
        fields = (
            "first_name",
            "last_name",
        )

    def __init__(self, *args, first_name="", last_name="", required=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].widget = forms.TextInput(attrs={"value": first_name})
        self.fields["last_name"].widget = forms.TextInput(attrs={"value": last_name})
        self.fields["first_name"].required = required
        self.fields["last_name"].required = required


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = (
            "address",
            "city",
            "postal_code",
            "user",
        )

    def __init__(self, required=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].widget = forms.HiddenInput()
        self.fields["address"].required = required
        self.fields["city"].required = required
        self.fields["postal_code"].required = required


class AddressChoiceForm(forms.Form):
    addresses = forms.ModelChoiceField(
        widget=forms.RadioSelect,
        queryset=QuerySet(),
        label="",
        required=False,
    )

    def __init__(self, queryset=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if queryset is None:
            raise ValueError("Value of queryset can't be None")
        self.fields["addresses"].queryset = queryset
