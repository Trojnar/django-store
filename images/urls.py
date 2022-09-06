from django.urls import path
from .views import (
    ImageManagerView,
    ImageDeleteView,
)

urlpatterns = [
    path("images/<uuid:pk>/", ImageManagerView.as_view(), name="images_manager"),
    path(
        "images/<uuid:product_pk>/delete/<int:image_pk>/",
        ImageDeleteView.as_view(),
        name="image_delete",
    ),
]
