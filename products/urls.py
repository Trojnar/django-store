from django.urls import path
from .views import (
    CreateProductView,
    ProductListView,
    ProductDetailsView,
    SearchResultView,
    CreateProductView,
    EditProductDetailsView,
    EditReviewProductDetailsView,
    UpdateProductView,
    UploadImages,
)

urlpatterns = [
    path("", ProductListView.as_view(), name="product_list"),
    path(
        "<uuid:pk>/",
        ProductDetailsView.as_view(),
        name="product_details",
    ),
    # Class views with "Edit" prefix, refers to update which post form is on
    # product_details page's html.
    path(
        "<uuid:pk>/<str:edit>/",
        EditProductDetailsView.as_view(),
        name="product_edit",
    ),
    path(
        "<uuid:pk>/<str:edit>/<int:index>/",
        EditReviewProductDetailsView.as_view(),
        name="review_details_edit",
    ),
    path("search/", SearchResultView.as_view(), name="search_result"),
    path("create/", CreateProductView.as_view(), name="product_create"),
    path("update/<uuid:pk>/", UpdateProductView.as_view(), name="product_update"),
    path("imageupload/", UploadImages.as_view(), name="image_upload"),
]
