from django.urls import path
from .views import CreateReviewView

urlpatterns = [
    path("<uuid:pk>/", CreateReviewView.as_view(), name="review_create"),
]
