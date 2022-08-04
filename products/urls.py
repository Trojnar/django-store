from django.urls import path
from .views import (
    CreateProductView,
    ProductListView,
    ProductDetailsView,
    SearchResultView,
    CreateProductView,
)

urlpatterns = [
    path("", ProductListView.as_view(), name="product_list"),
    path(
        "<uuid:pk>/",
        ProductDetailsView.as_view(),
        name="product_details",
    ),
    path("search/", SearchResultView.as_view(), name="search_result"),
    path("create/", CreateProductView.as_view(), name="product_create"),
]
