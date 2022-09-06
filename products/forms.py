from django import forms
from products.models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "producer",
            "price",
        ]


# TODO: niepotrzebne
class ProductFormWithImage(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "producer",
            "price",
            "count",
        ]


class CheckboxForm(forms.Form):
    choices = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        choices=[],
        label="",
    )

    def __init__(self, choices=[], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["choices"].choices = choices
        # TODO https://stackoverflow.com/questions/7192540/validation-on-a-dynamically-s
        # et-multiplechoicefield-where-the-field-is-initiall
