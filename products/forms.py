from django import forms
from products.models import CartItem, Product, Image


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
