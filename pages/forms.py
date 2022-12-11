from django.forms import Form, MultipleChoiceField


class DisplayCategoryChoiceForm(Form):
    categories = MultipleChoiceField(
        label="",
        required=False,
        choices=[],
    )

    def __init__(self, choices, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categories"].choices = choices
