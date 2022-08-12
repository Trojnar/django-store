from django.urls import path
from .views import CreateReviewView, UpdateReviewView

urlpatterns = [
    path("<uuid:pk>/", CreateReviewView.as_view(), name="review_create"),
    path(
        "<int:pk>/",
        UpdateReviewView.as_view(),
        name="review_edit",
    ),
]
