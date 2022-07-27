from django.urls import path
from .views import ProductListView, ProductDetailsView

urlpatterns = [
    path("", ProductListView.as_view(), name="product_list"),
    path("<uuid:pk>/", ProductDetailsView.as_view(), name="product_details"),
]
