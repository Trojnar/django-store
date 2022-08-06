from django.urls import path
from .views import (
    CreateProductView,
    ProductListView,
    ProductDetailsView,
    SearchResultView,
    CreateProductView,
    EditProductDetailsView,
)

urlpatterns = [
    path("", ProductListView.as_view(), name="product_list"),
    path(
        "<uuid:pk>/",
        ProductDetailsView.as_view(),
        name="product_details",
    ),
    path(
        "<uuid:pk>/<str:edit>",
        EditProductDetailsView.as_view(),
        name="product_edit",
    ),
    path("search/", SearchResultView.as_view(), name="search_result"),
    path("create/", CreateProductView.as_view(), name="product_create"),
]
