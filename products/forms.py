from django import forms
from products.models import Product, Image


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
        ]


class ImageForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = [
            "product",
            "image",
        ]

    def __init__(self, *args, **kwargs):
        # form not requirred
        super().__init__(*args, **kwargs)
        self.fields["product"].required = False
        self.fields["image"].required = False
