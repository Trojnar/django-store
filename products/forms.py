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
        fields = {
            "image",
            "product",
            "place",
        }

    def __init__(self, *args, **kwargs):
        # form not requirred
        super().__init__(*args, **kwargs)
        self.fields["place"].required = False


class ImagesManagerUploadImageForm(forms.ModelForm):
    image = forms.ImageField(widget=forms.FileInput(attrs={"multiple": True}))
    product_pk = forms.UUIDField(widget=forms.HiddenInput(), required=True)

    class Meta:
        model = Image
        fields = {
            "image",
        }

    def __init__(self, initial=None, *args, **kwargs):
        if not initial:
            raise ValueError("Initial value for product_pk required")
        kwargs.update(
            {
                "initial": {
                    "product_pk": initial["product_pk"],
                }
            }
        )
        super().__init__(*args, **kwargs)
        # self.fields["image"].required = False


class ImagesManagerForm(forms.Form):
    image_pk = forms.IntegerField(widget=forms.HiddenInput(), required=True)
    product_pk = forms.UUIDField(widget=forms.HiddenInput(), required=True)

    def __init__(self, initial=None, *args, **kwargs):
        if not initial:
            raise ValueError("Initial values required")
        kwargs.update(
            {
                "initial": {
                    "image_pk": initial["image_pk"],
                    "product_pk": initial["product_pk"],
                }
            }
        )
        super().__init__(*args, **kwargs)


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


class CreateProductForm(CheckboxForm, ProductFormWithImage):
    pass
