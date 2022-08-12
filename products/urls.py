from django.urls import path
from .views import (
    ProductCreateView,
    ProductListView,
    ProductDetailsView,
    SearchResultView,
    EditProductDetailsView,
    EditReviewProductDetailsView,
    ProductUpdateView,
    ImagesUpload,
    ImageManagerView,
    ImageDeleteView,
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
    path("create/", ProductCreateView.as_view(), name="product_create"),
    path("update/<uuid:pk>/", ProductUpdateView.as_view(), name="product_update"),
    path("imageupload/", ImagesUpload.as_view(), name="images_upload"),
    path(
        "images/<uuid:pk>/",
        ImageManagerView.as_view(),
        name="images_manager",
    ),
    path(
        "images/<uuid:product_pk>/delete/<int:image_pk>",
        ImageDeleteView.as_view(),
        name="image_delete",
    ),
]
