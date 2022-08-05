from django.forms import ModelForm
from .models import Review
from products.models import Product


class ReviewCreationForm(ModelForm):
    class Meta:
        model = Review
        fields = ("review",)

    # def form_valid(self, form):
    #     review = form.save(commit=False)
    #     review.author = self.request.author
    #     review.producer = Review.objects.update(self.request.GET("pk"))
    #     review.save()
    #     form.save_m2m()
    #     return self.get_success_url()
