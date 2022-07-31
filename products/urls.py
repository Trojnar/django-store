from django.urls import path
from .views import ProductListView, ProductDetailsView, SearchResultView
from django.views.decorators.cache import cache_page

urlpatterns = [
    path("", cache_page(60 * 60)(ProductListView.as_view()), name="product_list"),
    path(
        "<uuid:pk>/",
        cache_page(60 * 60)(ProductDetailsView.as_view()),
        name="product_details",
    ),
    path("search/", SearchResultView.as_view(), name="search_result"),
]
