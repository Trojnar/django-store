from django import forms
from .models import CartItem


class RadioForm(forms.Form):
    choices = forms.MultipleChoiceField(
        widget=forms.RadioSelect(
            attrs={"name": "sadjkf"},
        ),
        choices=[],
        label="",
    )

    def __init__(
        self, choices=None, name=None, attrs={}, required=False, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        if choices is None:
            raise ValueError("Value of choices can't be None.")
        if name is None:
            raise ValueError("Name html attribute can't be None.")
        self.fields["choices"].widget_attrs = attrs
        self.fields["choices"].required = required

        # TODO change like this https://stackoverflow.com/questions/8801910/override-dja
        # ngo-form-fields-name-attr
        self.fields["choices"].choices = choices
        self.fields[name] = self.fields["choices"]
        del self.fields["choices"]


class CartItemForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ("count",)
